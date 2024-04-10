from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import UserRegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import assemblyai as aai
import librosa
import numpy as np
import csv
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import google.generativeai as genai
import os
from .models import UserSession
from django.contrib.auth.models import User
from .models import UserSession 
from .models import DebateConversations# Import your UserSession model

def handle_message(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        
        # Store user message in the database
        user_res = DebateConversations.objects.create(session_ID=request.session.session_key,
                                           user_id=request.user.id,
                                           sender='User',
                                           message=user_message)
        user_res.save()
        

        # Retrieve previous AI response
        previous_ai_response = DebateConversations.objects.filter( user_id=request.user.id,sender='AI').first()

        # Compare user message with previous AI response
        if previous_ai_response:
            # Perform comparison logic here and generate appropriate response
            ai_response = "This is an appropriate response based on the comparison."
        else:
            ai_response = "This is the first AI response."
  
        # Store AI response in the database
        Conversations =  DebateConversations.objects.create(session_ID=request.session.session_key,
                                           user_id=request.user.id,
                                           sender='AI',
                                           message=ai_response)
        Conversations.save()

        ai_response = "This is the AI response."


        return JsonResponse({'ai_response': ai_response})
    else:
        ai_response = "This is the AI response."
        return JsonResponse({'ai_response': ai_response})
def debate_page(request):
    username = request.user.username
    topic = request.GET.get('topic', '')  # Get the topic from the query parameters
    print(topic)
    return render(request, 'users/debate_stage.html', {'username': username, 'topic': topic})


def user_session_list(request):
    username = request.user.username

    # Retrieve all UserSession objects from the database
    user_sessions = UserSession.objects.filter(user_id=username)

    # Pass the user_sessions data to the template for rendering
    return render(request, 'users/user_session_list.html', {'user_sessions': user_sessions})

def selector_view(request):
    return render(request, 'users/selector.html')

def speech_feedback_view(request):
    return render(request, 'users/speechfeedback.html')
def debate_view(request):
    # Get the username
    username = request.user.username

    # Construct the initial text for the debate
    initial_text = f"(break the dialogue to several lines) User is {username} (it's just an intro), (u'r speaking to single user) and u'r asking to practice debate skill with me and the skills required for debate. What topic would you like to practice debate on?"

    # Configure and use the Generative AI model
    genai.configure(api_key='AIzaSyCAoMFP7QaUOvVSFAEmqkk_w1HHVmBI0_4')
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(initial_text)
    response2 = model.generate_content(f"{response.text} convert it into a single dialogue, dialogue alone no * ")
    initial_text = response2.text

    # Render the debate view template with the initial text
    return render(request, 'users/debate.html', {'initial_text': initial_text})

def debate_txt(request):
    if request.method == 'POST':
        input_text = request.POST.get('input_text')
        # Process the input_text as needed
        output_text = process_function(input_text)  # Call your processing function here
        return JsonResponse({'output_text': output_text})
    

prompts = {"content_feedback":"""Imagine you've just listened to a speech or presentation. Provide constructive
          feedback on the substance and relevance of the content presented. Consider aspects such as the accuracy
          of information, depth of research, quality of supporting evidence, and effectiveness of examples or anecdotes.
          Your feedback should help the speaker understand how well their message resonated with the audience and 
          suggest areas for improvement.""",
          "coherence_feedback":"""After listening to a speech or presentation, assess the organization and logical
          flow of ideas presented. Provide constructive feedback on how well the speaker transitioned between points,
          maintained a coherent structure, and connected ideas smoothly. Consider the clarity of transitions, the
          logical progression of ideas, and the overall coherence of the speech. Your feedback should help the speaker
          improve the clarity and effectiveness of their communication.""",
          "delivery":"""Reflecting on a recent speech or presentation you've observed, provide feedback on the delivery
          style of the speaker. Evaluate aspects such as vocal variety, pacing, and emphasis. Consider elements like 
          volume, pitch, intonation, and the use of pauses for emphasis or dramatic effect. Your feedback should offer
          insights into how the speaker can enhance their delivery to engage the audience more effectively and convey
          their message with greater impact"""}
@login_required()
def process_audio(request):

        if request.method == 'POST' and request.FILES.get('audio_file'):
            
            feedback_type = request.POST.get('feedback_type')
            prompt =prompts[feedback_type]
            

            # Get the uploaded audio file
            audio_file = request.FILES['audio_file']
            temporary_file_path = audio_file.temporary_file_path()
         

            genai.configure(api_key="AIzaSyDNXOw7CIcBb7zo7ILsIdQMwbaEOK8BoQQ")
                        
            model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
            my_filename = temporary_file_path # @param {type:"string"}
            my_file_display_name = "user_audio" # @param {type:"string"}

            my_file = genai.upload_file(path=my_filename,
                            display_name=my_file_display_name)
            print(f"Uploaded file '{my_file.display_name}' as: {my_file.uri}")
            

            
            transcript = model.generate_content(["transcribe the text", my_file])

            response = model.generate_content([prompt, my_file])
            genai.delete_file(my_file.name)
            print(f'Deleted {my_file.display_name}.')

            response2 =model.generate_content(f"{response.text} convert it into a single dialouge ")
            output_string = response.text
            username = request.user.username

         
        # Save the uploaded files and text data to the database
            try:
                # Assuming you have already defined user_id, transcript_text, and response_text
                user_session = UserSession.objects.create(user_id=username, audio_file=audio_file, audiotext=transcript.text, feedbacktext=response.text)
                user_session.save()
                # Print success message
                print("User session saved successfully!")
            except Exception as e:
                # Print any potential errors that occurred during save operation
                print("Error saving user session:", e)
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

