# Build OuterClient v6.3.5

Workflow:
`.github/workflows/build-binaries.yml`

Najważniejsza poprawka PyInstaller:

```text
--collect-all PIL
--hidden-import PIL.ImageTk
--hidden-import PIL._tkinter_finder
```

Artifacts:
- OuterClient-v6.3.5-AppImage
- OuterClient-v6.3.5-Windows
