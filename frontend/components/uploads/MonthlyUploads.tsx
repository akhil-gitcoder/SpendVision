"use client";

import { useRef, useState } from "react";
import { CalendarDays, CheckCircle2, Download, Eye, FileSpreadsheet, Plus, UploadCloud, X } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { useAsync } from "@/hooks/useAsync";
import { cn } from "@/lib/utils";
import { uploadDocuments, type SavedUpload, type UploadPreview } from "@/lib/uploads";
import DeleteUploadButton from "@/components/uploads/DeleteUploadButton";

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const buttonClass = "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50";
const message = (error: unknown) => error instanceof Error ? error.message : "Something went wrong. Please try again.";


export default function MonthlyUploads() {
  const [monthHighlight, setMonthHighlight] = useState(0);
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [monthIndex, setMonthIndex] = useState(today.getMonth());
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SavedUpload | null>(null);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const previewRequest = useRef(0);
  const history = useAsync(() => uploadDocuments.list(year), [year]);
  const documents = history.data ?? [];
  const month = `${year}-${String(monthIndex + 1).padStart(2, "0")}`;
  const label = `${MONTHS[monthIndex]} ${year}`;
  const selectedDocuments = documents.filter((document) => document.month === month);
  const [deleteNotice, setDeleteNotice] = useState<string | null>(null);

  function clearSelection() {
    setFile(null);
    setError(null);
    setResult(null);
    setDeleteNotice(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  function chooseFile(selected: File | undefined) {
    if (!selected || busy) return;
    setError(null);
    setResult(null);
    setFile(null);
    if (!selected.name.toLowerCase().endsWith(".csv")) {
      setError("Please choose a CSV file.");
    } else if (!selected.size || selected.size > 5 * 1024 * 1024) {
      setError("Choose a non-empty CSV file no larger than 5 MB.");
    } else {
      setFile(selected);
    }
  }

  async function upload() {
    if (!file || busy) return;
    setBusy(true);
    setProgress(0);
    setError(null);
    setResult(null);
    try {
      const saved = await uploadDocuments.save(file, month, setProgress);
      setResult(saved);
      setFile(null);
      if (fileInput.current) fileInput.current.value = "";
      history.refetch();
    } catch (err) {
      setError(message(err));
    } finally {
      setBusy(false);
    }
  }

  async function viewDocument(id: string) {
    const current = ++previewRequest.current;
    setPreview(null);
    setPreviewError(null);
    dialog.current?.showModal();
    try {
      const data = await uploadDocuments.preview(id);
      if (current === previewRequest.current) setPreview(data);
    } catch (err) {
      if (current === previewRequest.current) setPreviewError(message(err));
    }
  }

  return (
    <div>
      <PageHeader title="Upload Transactions" description="Organize your statements by month and revisit every file you upload." />
      <div className="p-4 md:p-8 space-y-6 max-w-7xl">
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Your monthly statements</h2>
              <p className="mt-1 text-xs text-slate-500">Choose a month to upload a CSV or view saved files.</p>
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-500">
              <CalendarDays size={16} /> Year
              <select aria-label="Statement year" value={year} disabled={busy} onChange={(event) => {
                setYear(Number(event.target.value)); clearSelection();
              }} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                {Array.from({ length: today.getFullYear() - 1898 }, (_, index) => today.getFullYear() + 1 - index).map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
            {MONTHS.map((name, index) => {
              const key = `${year}-${String(index + 1).padStart(2, "0")}`;
              const count = documents.filter((document) => document.month === key).length;
              return <button key={name} disabled={busy} aria-pressed={monthIndex === index} onClick={() => {
                setMonthIndex(index); clearSelection();
              }} className={cn("rounded-xl border p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-50",
                monthIndex === index ? "border-brand-500 bg-brand-50" : "border-slate-200 hover:border-brand-300 hover:bg-slate-50")}>
                <span className="flex items-center justify-between gap-2 text-sm font-semibold text-slate-800">
                  {name}{count > 0 && !history.loading && !history.error && <CheckCircle2 size={16} className="text-emerald-500" />}
                </span>
                <span className="block mt-2 text-xs text-slate-500">
                  {history.loading ? "Loading…" : history.error ? "History unavailable" : count ? `${count} file${count === 1 ? "" : "s"} saved` : "No files yet"}
                </span>
              </button>;
            })}
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <Card
  key={`upload-${month}-${monthHighlight}`}
  className="monthly-upload-card"
>
            <h2 className="text-sm font-semibold text-slate-900">Upload for {label}</h2>
            <p className="mt-1 mb-5 text-xs leading-relaxed text-slate-500">Use a CSV containing dates in this month. Additional files are added to the month; existing transactions are kept and duplicate rows are skipped.</p>
            <input ref={fileInput} type="file" accept=".csv,text/csv" aria-label="Choose transaction CSV" className="hidden" disabled={busy}
              onChange={(event) => { chooseFile(event.target.files?.[0]); event.target.value = ""; }} />
            <button type="button" disabled={busy} onClick={() => fileInput.current?.click()}
              onDragOver={(event) => { event.preventDefault(); if (!busy) setDragging(true); }}
              onDragLeave={() => setDragging(false)} onDrop={(event) => {
                event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0]);
              }} className={cn("w-full flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-5 py-10 text-center transition-colors disabled:opacity-60",
                dragging ? "border-brand-400 bg-brand-50" : "border-slate-200 hover:border-brand-300 bg-slate-50/40")}>
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600"><UploadCloud size={22} /></span>
              <span className="text-sm font-medium text-slate-700 break-all">{file ? file.name : "Drop your CSV here, or click to browse"}</span>
              <span className="text-xs text-slate-400">{file ? `${(file.size / 1024).toFixed(1)} KB · ready to upload` : "CSV files only · up to 5 MB"}</span>
            </button>
            <div className="flex flex-wrap gap-2 mt-4">
              <button disabled={!file || busy} onClick={upload} className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50">
                <Plus size={16} />{busy ? progress === 100 ? "Processing transactions…" : `Uploading ${progress}%` : `Upload to ${MONTHS[monthIndex]}`}
              </button>
              {file && <button disabled={busy} onClick={clearSelection} className={buttonClass}>Clear</button>}
            </div>
            {busy && <progress aria-label="Upload progress" value={progress} max={100} className="w-full mt-4 h-2 accent-brand-500" />}
            {error && <p role="alert" className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-600">{error}</p>}
            {result && <div role="status" className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50 p-4">
              <p className="text-sm font-semibold text-emerald-800">File saved for {label}</p>
              <p className="mt-1 text-xs text-emerald-800">{result.imported_count} added · {result.duplicate_count} duplicates skipped · {result.failed_count} failed rows</p>
              {result.errors.length > 0 && <details className="mt-3 text-xs text-slate-600">
                <summary className="cursor-pointer">View row errors (up to 100)</summary>
                <ul className="mt-2 max-h-32 overflow-y-auto space-y-1">{result.errors.map((item, index) => <li key={index}>Row {item.row_number}: {item.reason}</li>)}</ul>
              </details>}
              <button className="mt-3 text-xs font-semibold text-brand-600 hover:underline" onClick={() => void viewDocument(result.id)}>View saved CSV</button>
            </div>}
          </Card>

          <Card
  key={`uploaded-files-${month}-${monthHighlight}`}
  className="monthly-upload-card"
>
            <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
              <div><h2 className="text-sm font-semibold text-slate-900">Uploaded files</h2><p className="text-xs text-slate-500 mt-1">{label}</p></div>
              <button disabled={busy} onClick={() => fileInput.current?.click()} className={buttonClass}><Plus size={15} />Add another CSV</button>
            </div>
            {deleteNotice && (
  <p
    role="status"
    className="mb-4 rounded-lg bg-emerald-50 p-3
      text-sm text-emerald-700"
  >
    {deleteNotice}
  </p>
)}
            {history.loading ? <p role="status" className="py-8 text-center text-sm text-slate-400">Loading saved files…</p> : history.error ? <div role="alert" className="text-sm text-rose-600">
              <p>{history.error}</p><button onClick={history.refetch} className="mt-3 text-brand-600 underline">Retry file list</button>
            </div> : selectedDocuments.length === 0 ? <div className="rounded-xl bg-slate-50 px-5 py-10 text-center">
              <FileSpreadsheet size={28} className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-medium text-slate-600">No files for {MONTHS[monthIndex]} yet</p>
              <p className="mt-1 text-xs text-slate-400">Upload a statement to keep it here.</p>
            </div> : <ul className="space-y-3">{selectedDocuments.map((document) => <li key={document.id} className="rounded-xl border border-slate-200 p-4">
              <div className="flex items-start gap-3"><FileSpreadsheet size={20} className="shrink-0 text-brand-500 mt-0.5" /><div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-800" title={document.filename}>{document.filename}</p>
                <p className="mt-1 text-xs text-slate-400">{new Date(document.uploaded_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })} · {(document.size_bytes / 1024).toFixed(1)} KB</p>
                <p className="mt-2 text-xs text-slate-500">{document.imported_count} added · {document.duplicate_count} duplicates · {document.failed_count} failed</p>
              </div></div>
              <div className="flex flex-wrap gap-2 mt-3">
  <button
    onClick={() => void viewDocument(document.id)}
    className={buttonClass}
  >
    <Eye size={14} />
    View CSV
  </button>

  <a
    href={uploadDocuments.downloadUrl(document.id)}
    download
    className={buttonClass}
  >
    <Download size={14} />
    Download
  </a>

  <DeleteUploadButton
    document={document}
    disabled={busy}
    onDeleted={() => {
      setResult((current) =>
        current?.id === document.id ? null : current
      );
      history.refetch();
    }}
  />
</div>
            
            </li>)}</ul>}
            <p className="mt-4 text-xs leading-relaxed text-slate-400">Only your account can access these files. File history starts with uploads made using this monthly upload page.</p>
          </Card>
        </div>

        <Card>
          <h2 className="text-sm font-semibold text-slate-900">CSV format</h2>
          <p className="mt-1 mb-3 text-xs text-slate-500">Required columns: date, description, amount, type. Keep each file within the selected month.</p>
          <pre className="overflow-x-auto rounded-lg bg-slate-50 p-4 text-xs text-slate-600">{`date,description,amount,type\n${month}-01,Swiggy,450,expense\n${month}-02,Uber,280,expense\n${month}-03,Salary,65000,income`}</pre>
        </Card>
      </div>

      <dialog ref={dialog} aria-labelledby="preview-title" onClose={() => { ++previewRequest.current; }} className="w-[calc(100%_-_2rem)] max-w-5xl rounded-2xl border border-slate-200 p-0 shadow-xl backdrop:bg-slate-900/40">
        <div className="flex items-center justify-between gap-4 border-b border-slate-200 p-5">
          <div className="min-w-0"><h2 id="preview-title" className="truncate font-semibold text-slate-900">{preview?.document.filename ?? "CSV preview"}</h2>
            <p className="text-xs text-slate-500 mt-1">Preview up to 100 rows and 20 columns. Long cells are shortened.</p></div>
          <button aria-label="Close preview" className={buttonClass} onClick={() => dialog.current?.close()}><X size={18} /></button>
        </div>
        <div className="p-5">
          {previewError ? <p role="alert" className="text-sm text-rose-600">{previewError}</p> : !preview ? <p role="status" className="text-sm text-slate-500">Loading document…</p> : <>
            <div className="overflow-auto max-h-[55vh] rounded-lg border border-slate-200">
              <table className="w-full text-left text-xs"><thead className="sticky top-0 bg-slate-50"><tr>{preview.columns.map((column, index) => <th key={index} className="px-3 py-3 font-semibold text-slate-700 whitespace-nowrap">{column}</th>)}</tr></thead>
                <tbody>{preview.rows.map((row, rowIndex) => <tr key={rowIndex} className="border-t border-slate-100">{row.map((cell, columnIndex) => <td key={columnIndex} className="px-3 py-2 text-slate-600 whitespace-pre-wrap min-w-[100px] max-w-xs break-words">{cell}</td>)}</tr>)}</tbody>
              </table>
            </div>
            <p className="text-xs text-slate-400 mt-3">Showing {preview.rows.length} of {preview.document.total_rows} rows. {preview.has_more ? "Download the original CSV to see everything." : "The original CSV is available below."}</p>
            {preview.document.errors.length > 0 && <details className="mt-3 text-xs text-slate-600"><summary className="cursor-pointer">Import errors (up to 100)</summary><ul className="mt-2 max-h-24 overflow-auto">{preview.document.errors.map((item, index) => <li key={index}>Row {item.row_number}: {item.reason}</li>)}</ul></details>}
            <a href={uploadDocuments.downloadUrl(preview.document.id)} download className={`${buttonClass} mt-4`}><Download size={15} />Download original CSV</a>
            
          </>}
        </div>
      </dialog>
    </div>
  );
}