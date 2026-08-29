---
name: github-markdown-note-style
description: GitHub Markdown & Obsidian Warm Sepia Dark Minimalist Design System for PySide6 / Qt Desktop Applications
---

# GitHub Markdown & Obsidian Warm Sepia Minimalist Design Skill

This skill provides design patterns, color palettes, and QSS styling rules for building ultra-clean, minimalist markdown note-taking interfaces in PySide6 / Qt6 inspired by GitHub Dark, Obsidian, and Warm Sepia document editors.

## Core Design Principles

1. **Rich Text Formatting Toolbar**:
   - Note editor includes a text formatting strip supporting **Bold**, **Italic**, **Underline**, **Font Size Selector**, and **Color Picker** for selected text lines.

2. **High Contrast Readable Transcript Boxes**:
   - Transcript and AI Summary text boxes MUST explicitly use `#FAF8F5` warm paper background with `#1C1917` dark high-contrast readable text color to prevent unreadable light text.

3. **Audio Track Selector for Transcription**:
   - Transcript view includes a track selection dropdown allowing users to transcribe either all tracks or a specific voice clip.

4. **Strict Monochrome Iconography (NO Colorful Emojis)**:
   - Use strictly **Monochrome / Black & White** text indicators, minimal monochrome Unicode symbols (`+`, `×`, `—`, `•`), or clean vector SVGs.

5. **High Contrast Warm Paper Reading Canvas**:
   - Canvas Background: `#FAF8F5` (Warm Cream Paper)
   - Primary Text: `#1C1917` (Dark Charcoal)
   - Selection Color: `#E6C5A8` (Warm Amber Accent)
   - Line Height: `1.6` with `14px` font size

6. **Warm Charcoal Control Shell**:
   - Deep Background: `#161412`
   - Panels & Sidebars: `#201D1A`
   - Borders: `#332E28`
   - Warm Amber Accent: `#D4A373` / `#8B5E3C`

## PySide6 QSS Color System Token Table

| Token | Color Code | Usage |
|---|---|---|
| Main Window Background | `#161412` | Shell outer background |
| Sidebar & Header | `#201D1A` | Navigation panels & toolbars |
| Border Lines | `#332E28` | Subtle layout separators |
| Primary Amber Accent | `#D4A373` | Active tab highlights, glowing focus |
| Button Primary | `#8B5E3C` | Action buttons |
| Note Paper Background | `#FAF8F5` | Main document canvas |
| Note Text Color | `#1C1917` | High contrast readable document body |
