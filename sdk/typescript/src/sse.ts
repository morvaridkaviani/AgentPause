/** Minimal incremental parser for `text/event-stream` (Server-Sent Events). */

export interface SseMessage {
  /** Event name (`"message"` when the server sent none). */
  event: string;
  data: string;
  /** Last event id seen on the stream, if any. */
  id: string | null;
}

export class SseParser {
  private buffer = "";
  private data: string[] = [];
  private event = "";
  private lastId: string | null = null;

  /** Feed decoded text; returns every message completed by it. */
  push(text: string): SseMessage[] {
    this.buffer += text;
    const messages: SseMessage[] = [];
    for (;;) {
      const index = this.buffer.search(/\r\n|\r|\n/);
      if (index < 0) break;
      // A trailing "\r" may be the first half of "\r\n": wait for more input.
      if (this.buffer[index] === "\r" && index === this.buffer.length - 1) break;
      const separator = this.buffer.startsWith("\r\n", index) ? 2 : 1;
      const line = this.buffer.slice(0, index);
      this.buffer = this.buffer.slice(index + separator);
      const message = this.line(line);
      if (message) messages.push(message);
    }
    return messages;
  }

  private line(line: string): SseMessage | null {
    if (line === "") return this.dispatch();
    if (line.startsWith(":")) return null; // comment / keep-alive
    const colon = line.indexOf(":");
    const field = colon < 0 ? line : line.slice(0, colon);
    let value = colon < 0 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") this.event = value;
    else if (field === "data") this.data.push(value);
    else if (field === "id" && !value.includes("\0")) this.lastId = value;
    return null;
  }

  private dispatch(): SseMessage | null {
    const message =
      this.data.length > 0 ? { event: this.event || "message", data: this.data.join("\n"), id: this.lastId } : null;
    this.data = [];
    this.event = "";
    return message;
  }
}
