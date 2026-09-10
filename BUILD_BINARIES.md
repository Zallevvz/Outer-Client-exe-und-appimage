# Build OuterClient v5.6

Workflow:
`.github/workflows/build-binaries.yml`

Najważniejsza poprawka PyInstaller:

```text
--collect-all PIL
--hidden-import PIL.ImageTk
--hidden-import PIL._tkinter_finder
```

Artifacts:
- OuterClient-v5.6-AppImage
- OuterClient-v5.6-Windows
