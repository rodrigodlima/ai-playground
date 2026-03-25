# How to add sound effects to Claude Code with hooks

## TLDR

Claude Code lets you hook shell commands into lifecycle events — session start, prompts, completions, and more. I took that a little too literally and added Age of Empires sound effects to each one. Somehow, coding feels a lot more epic now.

## Why sounds

It is normal to write a prompt in Claude Code and switch to another window to work on another task. While you are waiting for Claude Code to finish, you keep working elsewhere — but when you go back, it is waiting for a confirmation. That is annoying and wastes a lot of time. With sounds configured, you instantly know whether Claude is waiting for input or has already finished the task. Very handy, in my opinion.

## Configure the Hooks

You need to create a ```settings.json``` file at ```~/.claude/settings.json```

Hooks fire on specific lifecycle events:

* <font color="red">SessionStart</font>: When a new Claude Code session begins
* <font color="red">UserPromptSubmit</font>: Right after you hit enter on a prompt
* <font color="red">Stop</font>: When Claude finishes its response
* <font color="red">PreCompact</font>: Before context compaction happens (when the conversation gets too long)

## My setup

I used afplay, a macOS built-in audio player, to play the sounds. There are many sounds in /System/Library/Sounds/

```
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Task completed!\" with title \"Claude Code\"' && afplay /System/Library/Sounds/Hero.aiff"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"I need your attention!\" with title \"Claude Code\"' && afplay /System/Library/Sounds/Glass.aiff"
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Waiting for your permission!\" with title \"Claude Code\"' && afplay /System/Library/Sounds/Ping.aiff"
          }
        ]
      }
    ]
  }
}
```