"use client";

import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Cell, PieChart, Pie,
} from "recharts";
import { formatCompact } from "../lib/dashboard-utils";

const CHART_COLORS = ["#c8a84b", "#1fcec3", "#22c55e", "#7c6fe0", "#f59e0b", "#ef4444", "#a78bfa", "#67e8f9"];

function CustomTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{label}</div>
      <div className="chart-tooltip-value">{formatter ? formatter(payload[0].value) : payload[0].value}</div>
    </div>
  );
}

/* ─── Bar Chart Card ──────────────────────────────── */
function ChartCard({ title, data, dataKey, formatter, color }) {
  const chartData = data.slice(0, 8).map((item) => ({
    name: item.title.length > 12 ? `${item.title.slice(0, 12)}…` : item.title,
    fullName: item.title,
    value: Number(item[dataKey]) || 0,
  }));

  return (
    <div className="chart-card">
      <div className="chart-card-title">{title}</div>
      <div className="chart-card-body">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "var(--muted)", fontSize: 10 }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fill: "var(--muted)", fontSize: 10 }} tickLine={false} axisLine={false} width={50}
              tickFormatter={(v) => formatter ? formatter(v) : v} />
            <Tooltip content={<CustomTooltip formatter={formatter} />} cursor={{ fill: "rgba(200,168,75,0.06)" }} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={32}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={color || CHART_COLORS[i % CHART_COLORS.length]} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/* ─── Pie Chart Card ─────────────────────────────── */
function PieChartCard({ title, data }) {
  const chartData = data.slice(0, 6).map((item, i) => ({
    name: item.title,
    value: item.count,
    fill: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <div className="chart-card">
      <div className="chart-card-title">{title}</div>
      <div className="chart-card-body">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%"
              innerRadius={50} outerRadius={80} paddingAngle={3}
              stroke="var(--bg)" strokeWidth={2}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pie-legend">
          {chartData.map((d) => (
            <div key={d.name} className="pie-legend-item">
              <span className="pie-dot" style={{ background: d.fill }} />
              <span className="pie-legend-name">{d.name}</span>
              <span className="pie-legend-value">{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Location Charts ────────────────────────────── */
function LocationCharts({ language, items }) {
  const isEnglish = language === "en";
  return (
    <div className="analytics-chart-grid">
      <ChartCard
        title={isEnglish ? "Hotels by location" : "Số KS theo tỉnh"}
        data={items} dataKey="count"
        color="#c8a84b"
        formatter={(v) => v}
      />
      <ChartCard
        title={isEnglish ? "Avg best price" : "Giá TB thấp nhất"}
        data={items} dataKey="avgPrice"
        color="#1fcec3"
        formatter={(v) => formatCompact(v, language)}
      />
      <PieChartCard
        title={isEnglish ? "Market share" : "Tỉ lệ thị trường"}
        data={items}
      />
    </div>
  );
}

/* ─── Location Cards ──────────────────────────────── */
function LocationCards({ language, items, onSelectLocation }) {
  const isEnglish = language === "en";
  return (
    <div className="loc-cards">
      {items.map((item) => (
        <button key={item.id} type="button" className="loc-card" onClick={() => onSelectLocation?.(item.title)}>
          <div className="loc-card-head">
            <span className="loc-name">{item.title}</span>
            <span className="loc-badge">{item.count}</span>
          </div>
          <div className="loc-stats">
            <div className="loc-stat">
              <div className="loc-stat-label">{isEnglish ? "Avg price" : "Giá TB"}</div>
              <div className="loc-stat-value teal">{formatCompact(item.avgPrice, language)}</div>
            </div>
            <div className="loc-stat">
              <div className="loc-stat-label">{isEnglish ? "Max com" : "Com tốt nhất"}</div>
              <div className="loc-stat-value gold">{formatCompact(item.maxCommission, language)}</div>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

/* ─── Sender Cards ────────────────────────────────── */
function SenderCards({ language, items }) {
  const isEnglish = language === "en";
  const scale = items.length ? Math.max(...items.map((i) => i.count || 0), 1) : 1;

  return (
    <div className="sender-cards-grid">
      {items.map((item, index) => {
        const tone = CHART_COLORS[index % CHART_COLORS.length];
        return (
          <div key={item.id} className="sender-card">
            <div className="sender-card-head">
              <div className="sender-avatar" style={{ background: `${tone}22`, color: tone }}>
                {(item.title || "?")[0].toUpperCase()}
              </div>
              <div className="sender-main">
                <div className="sender-title">{item.title}</div>
                {item.subtitle ? <div className="sender-sub">{item.subtitle}</div> : null}
              </div>
              <div className="sender-count" style={{ color: tone }}>
                <div className="sender-count-value">{item.count}</div>
                <div className="sender-count-label">{isEnglish ? "offers" : "lựa chọn"}</div>
              </div>
            </div>

            <div className="sender-progress">
              <div
                className="sender-progress-fill"
                style={{
                  width: `${Math.max(6, Math.round((item.count / scale) * 100))}%`,
                  background: `linear-gradient(90deg, ${tone}44, ${tone})`,
                }}
              />
            </div>

            <div className="sender-stats">
              <div className="sender-stat">
                <div className="sender-stat-label">{isEnglish ? "Share" : "Tỉ lệ"}</div>
                <div className="sender-stat-value">{item.share}%</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Main AnalyticsView ──────────────────────────── */
export default function AnalyticsView({ language, title, subtitle, items, variant, onSelectLocation }) {
  const isEnglish = language === "en";

  return (
    <section>
      <div className="ph">
        <div className="ph-left">
          <h1>{title} <em>{isEnglish ? "overview" : "tổng quan"}</em></h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>

      {variant === "locations" ? (
        <>
          <LocationCharts language={language} items={items} />
          <LocationCards language={language} items={items} onSelectLocation={onSelectLocation} />
        </>
      ) : null}

      {variant === "senders" ? (
        <SenderCards language={language} items={items} />
      ) : null}
    </section>
  );
}