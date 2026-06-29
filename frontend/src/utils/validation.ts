import { hasUncaughtExceptionCaptureCallback } from "node:process";



export const isValidWebUrl = (urlString: string) : boolean => {
  try {

    if (urlString === undefined || urlString === null)
      return false;

    if (urlString.length === 0)
      return false;

    const url = new URL(urlString);

    const hasWebProtocol = url.protocol === "http:" || url.protocol === "https:";
    const isNotLocal = url.hostname !== "localhost";
    const isNotLocalLookup = url.hostname !== "127.0.0.1";

    return hasWebProtocol && isNotLocal && isNotLocalLookup;

  } catch {
    return false;
  }
}
