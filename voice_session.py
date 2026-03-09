"""
Voice session configuration for Gemini Live API integration.

This module defines the Live API model, config, and transcript state
management for the voice query feature. The frontend voice component
connects via WebSocket to Gemini Live, and the finalized transcript
is passed to process_business_question() in app.py.
"""

# Model name — update to match your AI Studio project's available model
LIVE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

LIVE_CONFIG = {
    "response_modalities": ["AUDIO"],
    "input_audio_transcription": {},
    "output_audio_transcription": {},
    "system_instruction": (
        "You are a voice assistant for a business intelligence dashboard. "
        "Listen to the user's spoken analytics question, restate it briefly, "
        "and produce a clean text query for the dashboard engine."
    ),
    "realtime_input_config": {
        "activity_handling": "START_OF_ACTIVITY_INTERRUPTS",
        "automatic_activity_detection": {
            "disabled": False,
            "prefix_padding_ms": 20,
            "silence_duration_ms": 200,
        },
    },
}

# Audio format constants (Google Live API spec)
INPUT_SAMPLE_RATE = 16000   # PCM 16-bit LE, mono, 16 kHz input
OUTPUT_SAMPLE_RATE = 24000  # PCM 16-bit LE, mono, 24 kHz output
INPUT_MIME_TYPE = "audio/pcm;rate=16000"


class TranscriptState:
    """Tracks the current voice session transcript."""

    def __init__(self):
        self.user_transcript = ""
        self.model_transcript = ""
        self.is_finalized = False
        self.interrupted = False

    def on_user_transcript(self, text):
        self.user_transcript += text

    def on_model_transcript(self, text):
        self.model_transcript += text

    def on_interruption(self):
        self.interrupted = True
        self.model_transcript = ""

    def finalize(self):
        self.is_finalized = True
        return self.user_transcript.strip()

    def reset(self):
        self.user_transcript = ""
        self.model_transcript = ""
        self.is_finalized = False
        self.interrupted = False
