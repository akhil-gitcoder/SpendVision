"use client";

import { useState } from "react";
import { Loader2, Trash2 } from "lucide-react";
import {
  uploadDocuments,
  type UploadedDocument,
} from "@/lib/uploads";

export default function DeleteUploadButton({
  document,
  disabled,
  onDeleted,
}: {
  document: UploadedDocument;
  disabled: boolean;
  onDeleted: (count: number) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function remove() {
    if (deleting || disabled) return;

    const confirmed = window.confirm(
      `Delete "${document.filename}"?\n\n` +
      `This permanently deletes the saved CSV and any remaining ` +
      `transactions it originally added ` +
      `(${document.imported_count} at upload time). ` +
      `Your totals will change.\n\n` +
      `Rows skipped as duplicates belong to earlier imports ` +
      `and are not deleted by this action. This cannot be undone.`
    );

    if (!confirmed) return;

    setDeleting(true);
    setError(null);

    try {
      const result = await uploadDocuments.remove(document.id);
      onDeleted(result.deleted_transactions);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not delete this upload."
      );
      setDeleting(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        disabled={disabled || deleting}
        onClick={() => void remove()}
        className="inline-flex items-center justify-center gap-2
          rounded-lg border border-rose-200 bg-white px-3 py-2
          text-sm font-medium text-rose-600 hover:bg-rose-50
          disabled:cursor-not-allowed disabled:opacity-50"
      >
        {deleting ? (
          <Loader2 size={14} className="animate-spin" />
        ) : (
          <Trash2 size={14} />
        )}

        {deleting ? "Deleting…" : "Delete"}
      </button>

      {error && (
        <p
          role="alert"
          className="mt-2 max-w-sm text-xs text-rose-600"
        >
          {error}
        </p>
      )}
    </div>
  );
}