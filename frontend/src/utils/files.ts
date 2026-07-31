const ACCEPTED_EXTENSIONS = [".csv", ".xlsx"];

export function isAcceptedAssetFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
}
