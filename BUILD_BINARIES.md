# Build OuterClient v4.9.4

Workflow:
`.github/workflows/build-binaries.yml`

Najważniejsza poprawka PyInstaller:

```text
--collect-all PIL
--hidden-import PIL.ImageTk
--hidden-import PIL._tkinter_finder
```

Artifacts:
- OuterClient-v4.9.4-AppImage
- OuterClient-v4.9.4-Windows
