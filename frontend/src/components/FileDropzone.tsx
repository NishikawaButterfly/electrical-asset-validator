import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { isAcceptedAssetFile } from "../utils/files";
import { Icon } from "./Icons";

const ACCEPT_ATTRIBUTE =
  ".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

interface FileDropzoneProps {
  id: string;
  label: string;
  description: string;
  file: File | null;
  disabled?: boolean;
  onFileChange: (file: File | null) => void;
  onInvalidFile: (message: string) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileDropzone({
  id,
  label,
  description,
  file,
  disabled = false,
  onFileChange,
  onInvalidFile,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const selectFile = (candidate?: File) => {
    if (!candidate) return;

    if (!isAcceptedAssetFile(candidate)) {
      onInvalidFile("Choose a CSV or XLSX file.");
      return;
    }

    onFileChange(candidate);
  };

  const handleInput = (event: ChangeEvent<HTMLInputElement>) => {
    selectFile(event.target.files?.[0]);
    event.target.value = "";
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    if (!disabled) selectFile(event.dataTransfer.files[0]);
  };

  return (
    <div className="file-field">
      <div className="file-field__heading">
        <label htmlFor={id}>{label}</label>
        <span>CSV or XLSX</span>
      </div>
      <p className="file-field__description" id={`${id}-description`}>
        {description}
      </p>

      {file ? (
        <div className="selected-file">
          <span className="selected-file__icon">
            <Icon name="file" />
          </span>
          <span className="selected-file__details">
            <strong title={file.name}>{file.name}</strong>
            <small>{formatBytes(file.size)}</small>
          </span>
          <button
            aria-label={`Remove ${file.name}`}
            className="icon-button"
            disabled={disabled}
            onClick={() => onFileChange(null)}
            type="button"
          >
            <Icon name="x" />
          </button>
        </div>
      ) : (
        <div
          className={`dropzone${isDragging ? " dropzone--active" : ""}`}
          onDragEnter={(event) => {
            event.preventDefault();
            if (!disabled) setIsDragging(true);
          }}
          onDragLeave={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget as Node)) {
              setIsDragging(false);
            }
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleDrop}
        >
          <span className="dropzone__icon">
            <Icon name="upload" />
          </span>
          <div>
            <strong>Drop your file here</strong>
            <p>or choose it from your computer</p>
          </div>
          <button
            className="button button--secondary button--small"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
            type="button"
          >
            Choose file
          </button>
        </div>
      )}

      <input
        ref={inputRef}
        accept={ACCEPT_ATTRIBUTE}
        aria-describedby={`${id}-description`}
        className="sr-only"
        disabled={disabled}
        id={id}
        onChange={handleInput}
        type="file"
      />
    </div>
  );
}
