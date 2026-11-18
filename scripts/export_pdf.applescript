-- usage: osascript scripts/export_pdf.applescript /abs/in.pptx /abs/out.pdf
on run argv
  set inFile to POSIX file (item 1 of argv)
  set outFile to POSIX file (item 2 of argv)
  tell application "Keynote"
    set d to open inFile
    export d to outFile as PDF
    close d saving no
  end tell
end run
