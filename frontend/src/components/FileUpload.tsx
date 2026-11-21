import { useState, type ChangeEvent, type DragEvent } from "react";

interface Props {
  disabled: boolean;
  onFileSelected: (file: File) => void;
}

export default function FileUpload({ disabled, onFileSelected }: Props) {
  const [dragging, setDragging] = useState(false);

  function onChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onFileSelected(file);
    event.target.value = ""; // allow selecting the same file again
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file && !disabled) onFileSelected(file);
  }

  return (
    <label
      className={`upload${dragging ? " upload--dragging" : ""}${disabled ? " upload--disabled" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <input type="file" accept=".mid,.midi,audio/midi" disabled={disabled} onChange={onChange} />
      <span className="upload__button">Choose MIDI file</span>
      <span className="upload__hint">or drop it here (.mid, .midi)</span>
    </label>
  );
}
