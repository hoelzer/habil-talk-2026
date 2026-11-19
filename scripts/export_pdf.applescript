-- usage: osascript scripts/export_pdf.applescript /abs/in.pptx /abs/out.pdf
-- The file is passed as an alias and the document taken as "front document": with Keynote 14.5
-- (Nov 2026), "set d to open (POSIX file …)" crashes Keynote while it converts the AppleEvent.
on run argv
  set inAlias to (POSIX file (item 1 of argv)) as alias
  set outPath to item 2 of argv
  tell application "Keynote"
    activate
    open inAlias
    delay 3
    set d to front document
    export d to (POSIX file outPath) as PDF
    close d saving no
  end tell
end run
