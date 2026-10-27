"use client";

import React, { useState } from "react";
import { Plus, Minus, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface RegionData {
  id: string;
  name: string;
  revenue: string;
  growth: string;
  coordinates: { x: number; y: number }; // Percentage 0-100
  color: string;
  pulseColor: string;
  glowRadius: number;
}

interface WorldMapProps {
  regions: RegionData[];
  selectedRegionId?: string | null;
  onSelectRegion?: (id: string | null) => void;
  className?: string;
}

export function WorldMap({
  regions,
  selectedRegionId,
  onSelectRegion,
  className,
}: WorldMapProps) {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [hoveredRegion, setHoveredRegion] = useState<RegionData | null>(null);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.25, 2.0));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.25, 0.8));
  const handleResetZoom = () => setZoomLevel(1);

  return (
    <div
      className={cn(
        "relative w-full h-[230px] rounded-2xl bg-[#080d1a] border border-white/[0.06] overflow-hidden flex items-center justify-center select-none shadow-inner",
        className
      )}
    >
      {/* Background cyber grid lines */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#131e3615_1px,transparent_1px),linear-gradient(to_bottom,#131e3615_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

      {/* Radial vignette */}
      <div className="absolute inset-0 bg-radial-vignette pointer-events-none" />

      {/* Zoomable & Pannable container */}
      <div
        className="relative w-full h-full flex items-center justify-center transition-transform duration-300 ease-out"
        style={{ transform: `scale(${zoomLevel})` }}
      >
        <svg
          viewBox="0 0 1000 500"
          className="w-full h-full object-contain filter drop-shadow-[0_0_12px_rgba(30,58,138,0.25)]"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Continent gradient fill */}
            <linearGradient id="continentGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1e293b" stopOpacity="0.85" />
              <stop offset="100%" stopColor="#0f172a" stopOpacity="0.95" />
            </linearGradient>

            {/* Glowing continent stroke */}
            <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.3" />
              <stop offset="50%" stopColor="#818cf8" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.3" />
            </linearGradient>

            {/* Network Arc Gradient */}
            <linearGradient id="networkArcGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.7" />
              <stop offset="50%" stopColor="#818cf8" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#c084fc" stopOpacity="0.7" />
            </linearGradient>

            {/* Radial glow filters for hubs */}
            <radialGradient id="cyanHalo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.7" />
              <stop offset="40%" stopColor="#06b6d4" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="blueHalo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.7" />
              <stop offset="40%" stopColor="#3b82f6" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="purpleHalo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#a855f7" stopOpacity="0.7" />
              <stop offset="40%" stopColor="#a855f7" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="amberHalo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.7" />
              <stop offset="40%" stopColor="#f59e0b" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="emeraldHalo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.7" />
              <stop offset="40%" stopColor="#10b981" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* ── Realistic Continents Geometry ── */}
          <g fill="url(#continentGrad)" stroke="url(#borderGrad)" strokeWidth="1.2" strokeLinejoin="round">
            {/* North America */}
            <path d="M 120,68 C 145,55 180,48 220,52 C 245,55 260,72 268,90 C 275,108 260,125 240,140 C 235,160 250,185 242,208 C 235,225 210,230 195,248 C 190,255 178,265 170,270 C 160,250 155,235 152,215 C 130,210 115,190 105,170 C 95,150 90,130 98,110 C 102,95 110,80 120,68 Z" />
            {/* Alaska & Northern Canada */}
            <path d="M 85,75 C 95,60 115,50 140,55 C 130,70 110,85 85,75 Z" />
            <path d="M 180,42 C 210,35 235,40 255,48 C 240,58 215,55 180,42 Z" />
            {/* Greenland */}
            <path d="M 330,40 C 355,30 385,38 395,58 C 390,80 370,105 348,100 C 335,88 330,60 330,40 Z" />

            {/* Central America & Caribbean */}
            <path d="M 170,270 C 178,278 190,290 205,305 C 200,312 190,310 182,300 C 175,290 168,280 170,270 Z" />
            <circle cx="230" cy="265" r="4" />
            <circle cx="245" cy="272" r="3" />

            {/* South America */}
            <path d="M 210,305 C 235,310 270,325 295,350 C 310,375 305,410 285,445 C 265,475 245,490 230,480 C 220,455 215,420 205,390 C 195,360 190,335 200,315 Z" />

            {/* Europe */}
            <path d="M 460,85 C 475,70 510,65 535,80 C 545,95 538,120 520,135 C 505,145 490,150 472,152 C 455,150 445,135 448,115 C 450,100 455,90 460,85 Z" />
            {/* Scandinavia */}
            <path d="M 488,48 C 502,40 518,45 528,62 C 520,80 505,100 495,95 C 485,82 482,60 488,48 Z" />
            {/* British Isles */}
            <path d="M 432,95 C 442,88 448,95 445,110 C 438,122 428,118 432,95 Z" />
            <path d="M 418,105 C 425,100 428,108 424,115 C 420,120 415,115 418,105 Z" />

            {/* Africa */}
            <path d="M 455,165 C 490,160 540,165 565,195 C 585,225 580,265 565,305 C 550,345 525,385 495,405 C 475,410 460,390 455,360 C 448,320 435,280 430,240 C 425,200 438,175 455,165 Z" />
            {/* Madagascar */}
            <path d="M 585,340 C 592,335 598,348 592,370 C 586,380 580,375 585,340 Z" />

            {/* Asia (Eurasia & Middle East) */}
            <path d="M 535,80 C 580,60 645,55 720,65 C 785,75 830,95 860,135 C 880,165 865,195 835,220 C 800,240 760,245 720,230 C 695,245 660,265 635,245 C 610,225 615,190 595,175 C 570,160 550,165 535,140 Z" />
            {/* Middle East peninsula */}
            <path d="M 565,195 C 590,190 610,205 618,230 C 615,250 590,265 572,250 C 560,235 558,210 565,195 Z" />
            {/* Indian Subcontinent */}
            <path d="M 660,225 C 690,220 720,235 728,265 C 720,295 690,325 675,320 C 660,300 650,260 660,225 Z" />
            {/* Southeast Asia */}
            <path d="M 750,235 C 775,230 790,250 795,280 C 780,298 765,285 750,265 Z" />
            {/* Japan */}
            <path d="M 875,145 C 885,140 892,150 885,170 C 878,185 868,175 875,145 Z" />
            {/* Indonesia / Philippines archipelago */}
            <circle cx="780" cy="310" r="5" />
            <circle cx="810" cy="320" r="6" />
            <circle cx="835" cy="315" r="4" />
            <circle cx="850" cy="290" r="5" />

            {/* Australia & Oceania */}
            <path d="M 800,360 C 835,340 880,350 905,380 C 915,415 895,450 860,460 C 825,465 790,445 780,410 C 775,385 785,370 800,360 Z" />
            {/* New Zealand */}
            <path d="M 935,440 C 942,435 948,445 942,460 C 935,470 928,460 935,440 Z" />
          </g>

          {/* ── Global Live Neural Network Arcs (Connecting Hubs) ── */}
          <g fill="none" stroke="url(#networkArcGrad)" strokeWidth="1.6" strokeDasharray="4 4" className="opacity-70">
            {/* North America -> Europe */}
            <path d="M 210,165 Q 340,90 480,120" />
            {/* Europe -> Asia Pacific */}
            <path d="M 480,120 Q 640,110 780,230" />
            {/* North America -> Latin America */}
            <path d="M 210,165 Q 230,270 255,380" />
            {/* Europe -> Middle East */}
            <path d="M 480,120 Q 530,170 585,225" />
            {/* Middle East -> Asia Pacific */}
            <path d="M 585,225 Q 680,210 780,230" />
          </g>

          {/* ── Animated Regional Pulse Beacons ── */}
          {regions.map((region) => {
            const isHovered = hoveredRegion?.id === region.id;
            const isSelected = selectedRegionId === region.id;
            // Map percentage coordinates (0-100) to SVG viewBox (0-1000, 0-500)
            const cx = (region.coordinates.x / 100) * 1000;
            const cy = (region.coordinates.y / 100) * 500;

            const haloGradientId =
              region.id === "na"
                ? "cyanHalo"
                : region.id === "eu"
                ? "blueHalo"
                : region.id === "apac"
                ? "purpleHalo"
                : region.id === "me"
                ? "amberHalo"
                : "emeraldHalo";

            return (
              <g
                key={region.id}
                className="cursor-pointer transition-transform duration-300"
                onClick={() => onSelectRegion?.(isSelected ? null : region.id)}
                onMouseEnter={() => setHoveredRegion(region)}
                onMouseLeave={() => setHoveredRegion(null)}
              >
                {/* Large Ambient Radial Glow (like in the screenshot mockup) */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered || isSelected ? 48 : region.glowRadius}
                  fill={`url(#${haloGradientId})`}
                  className="transition-all duration-300"
                />

                {/* Animated Pulsing Ring */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered || isSelected ? 18 : 12}
                  fill="none"
                  stroke={region.pulseColor}
                  strokeWidth="1.5"
                  className="animate-ping opacity-75"
                  style={{ animationDuration: "2.5s" }}
                />

                {/* Solid Core Dot */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered || isSelected ? 7 : 5}
                  fill={region.color}
                  stroke="#ffffff"
                  strokeWidth="2"
                  className="shadow-lg filter drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
                />

                {/* Label text on hover/active */}
                {(isHovered || isSelected) && (
                  <g className="animate-in fade-in duration-200">
                    <rect
                      x={cx - 45}
                      y={cy - 34}
                      width="90"
                      height="22"
                      rx="6"
                      fill="#070b16"
                      stroke={region.color}
                      strokeWidth="1"
                    />
                    <text
                      x={cx}
                      y={cy - 19}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize="10"
                      fontWeight="bold"
                      className="font-sans pointer-events-none"
                    >
                      {region.name}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Floating Tooltip if a node is hovered */}
      {hoveredRegion && (
        <div className="absolute top-3 left-3 rounded-xl border border-white/10 bg-[#090e1c]/95 px-3 py-2 shadow-2xl backdrop-blur-xl text-xs space-y-0.5 pointer-events-none z-10 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center gap-1.5 font-bold text-white">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: hoveredRegion.color }}
            />
            {hoveredRegion.name}
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-300">
            <span>Rev: <strong className="text-white">{hoveredRegion.revenue}</strong></span>
            <span className="text-emerald-400 font-semibold">{hoveredRegion.growth}</span>
          </div>
        </div>
      )}

      {/* Zoom and Reset Controls matching mockup */}
      <div className="absolute bottom-3 left-3 flex items-center rounded-xl border border-white/10 bg-[#0c1222]/90 backdrop-blur-md p-0.5 shadow-lg z-10">
        <button
          onClick={handleZoomIn}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
          title="Zoom in"
          aria-label="Zoom in"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
        <div className="h-3.5 w-px bg-white/10" />
        <button
          onClick={handleZoomOut}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
          title="Zoom out"
          aria-label="Zoom out"
        >
          <Minus className="h-3.5 w-3.5" />
        </button>
        <div className="h-3.5 w-px bg-white/10" />
        <button
          onClick={handleResetZoom}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
          title="Reset zoom"
          aria-label="Reset zoom"
        >
          <Maximize2 className="h-3 w-3" />
        </button>
      </div>

      {/* Legend Indicator */}
      <div className="absolute bottom-3 right-3 hidden sm:flex items-center gap-2 text-[10px] text-slate-400 bg-[#0c1222]/80 px-2 py-1 rounded-lg border border-white/5">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
        <span>Live Regional Activity</span>
      </div>
    </div>
  );
}
