import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const source = "C:/Users/BBY/Documents/Export eleve EPC.xlsx";
const input = await FileBlob.load(source);
const workbook = await SpreadsheetFile.importXlsx(input);

const sheetInfo = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 4000 });
console.log("SHEETS", sheetInfo.ndjson ?? JSON.stringify(sheetInfo));
for (const sheet of workbook.worksheets.items) {
  const used = sheet.getUsedRange(true);
  console.log("SHEET", sheet.name, "USED", used?.address ?? "none");
  if (used) {
    const rows = used.values.slice(0, 15).map((row) => row.slice(0, 40));
    console.log(JSON.stringify(rows));
  }
}
