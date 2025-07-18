import speech_recognition as sr

print("Microphones found:", sr.Microphone.list_microphone_names())
try:
    with sr.Microphone() as mic:
        print("Microphone is accessible!")
except Exception as e:
    print(f"Microphone access error: {e}") 