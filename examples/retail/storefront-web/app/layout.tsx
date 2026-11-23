// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import type { Metadata } from "next";
import { Instrument_Sans } from "next/font/google";
import "./globals.css";

const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "恒信牙科医疗器械",
  description: "与 恒信助手一起浏览 恒信牙科医疗器械商品目录。",
};

// 衬线字体栈用系统字体，避免构建时联网下载 Google 字体。
const displayFont =
  '"Songti SC", "STSong", "Noto Serif CJK SC", "Source Han Serif SC", Georgia, "Times New Roman", serif';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={instrumentSans.variable} style={{ ["--font-display" as string]: displayFont }}>
      <body>{children}</body>
    </html>
  );
}
