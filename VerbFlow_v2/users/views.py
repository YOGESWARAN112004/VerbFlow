from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import UserRegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import assemblyai as aai
import librosa
import numpy as np
import csv
import google.generativeai as genai
import os
from .models import UserSession


def selector_view(request):
    return render(request, 'users/selector.html')

def speech_feedback_view(request):
    return render(request, 'users/speechfeedback.html')

def debate_view(request):
        # Check if the user is authenticated
    if request.user.is_authenticated:
        # If authenticated, get the username
        username = request.user.username
    else:
        # If not authenticated, set a default username
        username = 'user'
    
    initial_text = f"(break the dialouge to several lines)user is {username}(it's just a intro ),(u'r speaking to single user) and u'r asking practice debate skill with me and the skills required for debate. and on what topic would u like to practice debate"
    genai.configure(api_key='AIzaSyCAoMFP7QaUOvVSFAEmqkk_w1HHVmBI0_4')

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(f"""{initial_text}
        """)
    response2 =model.generate_content(f"{response.text} convert it into a single dialouge, dialouge alone no * ")
    initial_text = response2.text
    return render(request, 'users/debate.html', {'initial_text': initial_text})

def debate_txt(request):
    if request.method == 'POST':
        input_text = request.POST.get('input_text')
        # Process the input_text as needed
        output_text = process_function(input_text)  # Call your processing function here
        return JsonResponse({'output_text': output_text})
    
def load_pitch_values(file_path):
    pitch_values = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            pitch_values.append(float(row[1]))
    return pitch_values


def calculate_pace(pitch_values):
    pace_values = []
    for i in range(1, len(pitch_values)):
        pitch_variation = abs(pitch_values[i] - pitch_values[i - 1])
        if pitch_variation < 500:  # Adjust the threshold as needed
            pace_values.append('Low')  # Low pace
        elif pitch_variation < 1500:
            pace_values.append('Medium')  # Medium pace
        else:
            pace_values.append('High')  # High pace
    return pace_values


def save_pace_values(pace_values, output_file):
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Pace'])
        for i, pace in enumerate(pace_values):
            writer.writerow([i, pace])


def calculate_pitch(signal, sample_rate, hop_length):
    # Compute pitch using autocorrelation method
    pitches, magnitudes = librosa.piptrack(y=signal, sr=sample_rate, hop_length=hop_length)

    # Take the maximum pitch (fundamental frequency) across time
    pitch_values = np.max(pitches, axis=0)

    return pitch_values




def save_pitch_values_to_csv(pitch_values, output_file):
    # Write pitch values to CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Index', 'Pitch (Hz)'])
        for i, pitch in enumerate(pitch_values):
            writer.writerow([i, pitch])


def csv_to_string(file_path):
            """
            Reads the contents of a CSV file and returns them as a single string.
            
            Args:
            - file_path (str): The path to the CSV file.
            
            Returns:
            - str: The contents of the CSV file as a single string.
            """
            # Initialize an empty string to store the result
            result = ""
            
            # Open the CSV file
            with open(file_path, newline='') as csvfile:
                # Create a CSV reader object
                reader = csv.reader(csvfile)
                
                # Iterate over each row in the CSV file
                for row in reader:
                    # Join the elements in the row with a comma and append it to the result string
                    result += ','.join(row) + '\n'
            
            # Return the resulting string
            return result
prompt = """Imagine you've just attended a speech or presentation. Reflecting on the experience, provide feedback to the speaker, encompassing various aspects:

Content Clarity: Was the main message clear and well-organized? Did you understand the key points easily?

Engagement Level: How engaging was the speaker? Did they capture your attention throughout the speech?

Delivery Style: Comment on the speaker's delivery style. Did they appear confident and authentic? How effective was their body language and eye contact?

Vocal Variety: Reflect on the speaker's use of vocal variety. Did they vary their pitch, pace, and volume appropriately?

Timing and Pace: Consider the pace of the speech. Was it too fast or too slow? Were pauses used effectively?

Language and Vocabulary: Evaluate the language used. Was it appropriate for the audience? Did it convey the intended message effectively?

Relevance and Depth: Assess the depth of content. Did the speech provide new insights or perspectives? Did it address the audience's needs or interests?

Visual Aids (if applicable): If visual aids were used, evaluate their effectiveness. Did they enhance understanding and engagement?

Overall Impact: Reflect on the overall impact of the speech. Did it leave a lasting impression? Did it inspire action or reflection?

Constructive Criticism(only if needed): Provide specific suggestions for improvement. Highlight areas where the speaker could enhance their delivery, content, or overall effectiveness."""

def process_audio(request):
    if request.user.is_authenticated:

        if request.method == 'POST' and request.FILES.get('audio_file'):
            # Get the uploaded audio file
            audio_file = request.FILES['audio_file']
            temporary_file_path = audio_file.temporary_file_path()

            aai.settings.api_key = "87c3ee6010a84c9f9ae6ca023a33d159"
            transcriber = aai.Transcriber()

            transcript = transcriber.transcribe(temporary_file_path)
            # transcript = transcriber.transcribe("./my-local-audio-file.wav")

            print(transcript.text)

            # Load audio file
            signal, sample_rate = librosa.load(temporary_file_path, sr=None)

            # Calculate the duration of the audio in minutes
            audio_duration_minutes = librosa.get_duration(y=signal, sr=sample_rate) / 60

            # Specify the desired number of pitch values per minute
            pitch_values_per_minute = 60

            # Calculate the total number of desired pitch values
            desired_pitch_values = int(audio_duration_minutes * pitch_values_per_minute)

            # Calculate the number of samples for each segment
            segment_length = len(signal) // desired_pitch_values

            # Calculate pitch for each segment
            pitch_values = []
            for i in range(desired_pitch_values):
                start_sample = i * segment_length
                end_sample = min((i + 1) * segment_length, len(signal))
                segment = signal[start_sample:end_sample]
                pitch = calculate_pitch(segment, sample_rate, len(segment))
                pitch_values.append(np.mean(pitch))  # Taking mean pitch value for the segment

            # Save pitch values to CSV file
            output_file = "pitch_values.csv"
            save_pitch_values_to_csv(pitch_values, output_file)

            print("Pitch values saved to:", output_file)

            # Load pitch values from CSV file
            pitch_file = "pitch_values.csv"  # Change to your file path
            pitch_values = load_pitch_values(pitch_file)

            # Calculate pace values
            pace_values = calculate_pace(pitch_values)

            # Save pace values to CSV file
            pace_file = "pace_values.csv"  # Output file path
            save_pace_values(pace_values, pace_file)

            print("Pace values saved to:", pace_file)

            # Example usage:
            file_path = r"C:\Users\yoges\VerbFlow_v1\pace_values.csv"
            file_path1= r"C:\Users\yoges\VerbFlow_v1\pitch_values.csv"
            pace_string = csv_to_string(file_path)
            pitch_string = csv_to_string(file_path1)


            genai.configure(api_key='AIzaSyCAoMFP7QaUOvVSFAEmqkk_w1HHVmBI0_4')

            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(f"""{transcript.text}.{prompt}/n{pace_string}
            /n{pitch_string}
            """)
            response2 =model.generate_content(f"{response.text} convert it into a single dialouge ")
            output_string = response.text
            # import pyttsx3

            # def text_to_speech(text):
            #     engine = pyttsx3.init()
            #     engine.say(text)
            #     engine.runAndWait()
            # text_to_speech(response2.text)        
                    # Return the output as a response
            user_id = request.session.session_key

        # Save the uploaded files and text data to the database
            try:
                # Assuming you have already defined user_id, transcript_text, and response_text
                user_session = UserSession.objects.create(user_id=user_id, audio_file=audio_file, audiotext=transcript.text, feedbacktext=response.text)
                user_session.save()
                # Print success message
                print("User session saved successfully!")
            except Exception as e:
                # Print any potential errors that occurred during save operation
                print("Error saving user session:", e)
            return render(request, 'users/feedback.html', {'output_string': output_string})
        else:
            return render(request, 'users/speechfeedback.html')
    else:
        if request.method == 'POST' and request.FILES.get('audio_file'):
            # Get the uploaded audio file
            audio_file = request.FILES['audio_file']
            temporary_file_path = audio_file.temporary_file_path()

            aai.settings.api_key = "87c3ee6010a84c9f9ae6ca023a33d159"
            transcriber = aai.Transcriber()

            transcript = transcriber.transcribe(temporary_file_path)
            # transcript = transcriber.transcribe("./my-local-audio-file.wav")

            print(transcript.text)

            # Load audio file
            signal, sample_rate = librosa.load(temporary_file_path, sr=None)

            # Calculate the duration of the audio in minutes
            audio_duration_minutes = librosa.get_duration(y=signal, sr=sample_rate) / 60

            # Specify the desired number of pitch values per minute
            pitch_values_per_minute = 60

            # Calculate the total number of desired pitch values
            desired_pitch_values = int(audio_duration_minutes * pitch_values_per_minute)

            # Calculate the number of samples for each segment
            segment_length = len(signal) // desired_pitch_values

            # Calculate pitch for each segment
            pitch_values = []
            for i in range(desired_pitch_values):
                start_sample = i * segment_length
                end_sample = min((i + 1) * segment_length, len(signal))
                segment = signal[start_sample:end_sample]
                pitch = calculate_pitch(segment, sample_rate, len(segment))
                pitch_values.append(np.mean(pitch))  # Taking mean pitch value for the segment

            # Save pitch values to CSV file
            output_file = "pitch_values.csv"
            save_pitch_values_to_csv(pitch_values, output_file)

            print("Pitch values saved to:", output_file)

            # Load pitch values from CSV file
            pitch_file = "pitch_values.csv"  # Change to your file path
            pitch_values = load_pitch_values(pitch_file)

            # Calculate pace values
            pace_values = calculate_pace(pitch_values)

            # Save pace values to CSV file
            pace_file = "pace_values.csv"  # Output file path
            save_pace_values(pace_values, pace_file)

            print("Pace values saved to:", pace_file)

            # Example usage:
            file_path = r"C:\Users\yoges\VerbFlow_v1\pace_values.csv"
            file_path1= r"C:\Users\yoges\VerbFlow_v1\pitch_values.csv"
            pace_string = csv_to_string(file_path)
            pitch_string = csv_to_string(file_path1)


            genai.configure(api_key='AIzaSyCAoMFP7QaUOvVSFAEmqkk_w1HHVmBI0_4')

            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(f"""{transcript.text}.{prompt}/n{pace_string}
            /n{pitch_string}
            """)
            response2 =model.generate_content(f"{response.text} convert it into a single dialouge ")
            output_string = response.text

                  
            return render(request, 'users/feedback.html', {'output_string': output_string})
        else:
            return render(request, 'users/speechfeedback.html')

def home(request):
    return render(request, 'users/home.html')



def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hi {username}, your account was created successfully')
            return redirect('home')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})



@login_required()
def profile(request):
    return render(request, 'users/profile.html')

