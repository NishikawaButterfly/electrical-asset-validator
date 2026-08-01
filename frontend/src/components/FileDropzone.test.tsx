import { describe, expect, it } from "vitest";
import { isAcceptedAssetFile } from "../utils/files";

describe("isAcceptedAssetFile", () => {
  it("accepts CSV and XLSX files regardless of extension casing", () => {
    expect(isAcceptedAssetFile(new File(["tag"], "assets.csv"))).toBe(true);
    expect(isAcceptedAssetFile(new File(["data"], "Revision-B.XLSX"))).toBe(true);
  });

  it("rejects unsupported file types", () => {
    expect(isAcceptedAssetFile(new File(["data"], "assets.xls"))).toBe(false);
    expect(isAcceptedAssetFile(new File(["data"], "drawing.pdf"))).toBe(false);
    expect(isAcceptedAssetFile(new File(["data"], "assets.csv.exe"))).toBe(false);
  });
});
