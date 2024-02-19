import os
import sys
from spleeter.separator import Separator
from pydub import AudioSegment

# Function to convert audio to MIDI using Aubio
def audio_to_midi(audio_path, midi_path):
    from aubio import source, notes, miditofreq, freqtomidi

    win_s = 512                 # window size for pitch analysis
    hop_s = win_s // 2           # hop size (overlap)
    samplerate = 44100

    # Open audio file with Aubio
    aubio_source = source(audio_path, samplerate, hop_s)
    samplerate = aubio_source.samplerate

    # Initialize pitch detection
    samplerate = aubio_source.samplerate
    tolerance = 0.8
    pitch_o = notes("default", win_s, hop_s, samplerate)
    pitch_o.set_unit("midi")
    pitch_o.set_tolerance(tolerance)

    # Create a MIDI file
    midi_file = open(midi_path, 'w')
    midi_file.write("0, 0, Header, 1, 1, 960\n")
    midi_file.write("1, 0, Start_track\n")

    # Process audio and write MIDI
    total_frames = 0
    while True:
        samples, read = aubio_source()
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()

        # Convert pitch to MIDI note
        midi_note = int(freqtomidi(pitch))

        # Write MIDI events
        if confidence > 0.5:
            midi_file.write(f"1, {total_frames}, Note_on_c, 0, {midi_note}, 64\n")
            total_frames += 100
            midi_file.write(f"1, {total_frames}, Note_off_c, 0, {midi_note}, 64\n")
            total_frames += 100

        if read < hop_s:
            break

    # Finalize MIDI file
    midi_file.write("1, 0, End_track\n")
    midi_file.write("0, 0, End_of_file\n")
    midi_file.close()

# Separate vocals and accompaniment using Spleeter
def separate_audio(input_path, output_path):
    separator = Separator('spleeter:2stems')
    separator.separate_to_file(input_path, output_path)

# Processing command line arguments
if len(sys.argv) == 2 and sys.argv[1] == "-run":
    # Get all .mp4 files in the current directory
    mp4_files = [file for file in os.listdir() if file.endswith(".mp4")]

    # Process each .mp4 file
    for mp4_file in mp4_files:
        # Extract audio from video
        output_audio_path = mp4_file.replace(".mp4", "_audio.wav")
        video_audio = AudioSegment.from_file(mp4_file, format='mp4')
        video_audio.export(output_audio_path, format='wav')

        # Separate vocals and accompaniment
        output_accompaniment_path = mp4_file.replace(".mp4", "_accompaniment.wav")
        separate_audio(output_audio_path, output_accompaniment_path)

        # Convert accompaniment to MIDI
        output_midi_path = mp4_file.replace(".mp4", "_accompaniment.mid")
        audio_to_midi(output_accompaniment_path, output_midi_path)

        print(f"Conversion complete for {mp4_file}")
else:
    print("Usage: python converter.py -run")
