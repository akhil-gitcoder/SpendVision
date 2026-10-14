import type { Metadata } from "next";
import MonthlyUploads from "@/components/uploads/MonthlyUploads";

export const metadata: Metadata = { title: "Upload" };

export default function UploadPage() {
  return <MonthlyUploads />;
}