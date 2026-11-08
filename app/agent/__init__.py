"""The website's runtime agent (Architecture C): the Visit Assistant.

    visitor question → agent.py → Gemini (+ tool descriptions)
                     → model asks for a tool → permissions.py → tools.py
                     → result back to the model → answer → answer check → browser
"""
