/** Triggers a browser download of `content` as a file named `filename`. */
export function downloadTextFile(filename: string, content: string, mimeType = "text/markdown") {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
