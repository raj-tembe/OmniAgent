/**
 * Editor-native actions: prompts pre-filled from real file content instead
 * of requiring the user to type context by hand. Kept separate from
 * FileTree.tsx so the prompt text itself is a plain, reviewable function —
 * no React, no fetch, just strings in and a string out.
 */

export type EditorAction = "explain" | "fix" | "test";

export const EDITOR_ACTIONS: { id: EditorAction; label: string }[] = [
  { id: "explain", label: "Explain" },
  { id: "fix", label: "Fix issues" },
  { id: "test", label: "Generate tests" },
];

export function composeActionPrompt(action: EditorAction, filePath: string, content: string): string {
  const fence = "```";
  const needsTrailingNewline = content.length > 0 && !content.endsWith("\n");
  const body = `${fence}\n${content}${needsTrailingNewline ? "\n" : ""}${fence}`;

  switch (action) {
    case "explain":
      return `Explain what the following file does, in plain language.\n\nFile: ${filePath}\n\n${body}`;
    case "fix":
      return `Review the following file for bugs, lint issues, and type errors, and fix anything you find.\n\nFile: ${filePath}\n\n${body}`;
    case "test":
      return `Write unit tests for the following file.\n\nFile: ${filePath}\n\n${body}`;
  }
}
