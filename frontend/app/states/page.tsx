import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { StatesGallery } from "@/components/states/StatesGallery";

export const metadata: Metadata = {
  title: "BillBack: every state",
  robots: { index: false, follow: false },
};

/** Dev page for screenshots: every message and failure state, EN and ES. Hidden in production builds. */
export default function StatesPage() {
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_SHOW_STATES !== "1") notFound();
  return <StatesGallery />;
}
