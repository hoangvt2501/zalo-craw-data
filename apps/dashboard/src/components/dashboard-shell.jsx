"use client";

import AnalyticsView from "./analytics-view";
import CompareDrawer from "./compare-drawer";
import DealsWorkspace from "./deals-workspace";
import DetailModal from "./detail-modal";
import Sidebar from "./sidebar";
import UnmatchedView from "./unmatched-view";
import { useDashboardState } from "../lib/hooks/use-dashboard-state";
import { useDetailModal } from "../lib/hooks/use-detail-modal";

export default function DashboardShell({ apiBaseUrl }) {
  const state = useDashboardState(apiBaseUrl);
  const detail = useDetailModal(apiBaseUrl);
  const isEnglish = state.language === "en";

  return (
    <>
      <div className="shell">
        <Sidebar
          activePage={state.activePage}
          hotelCount={state.acceptedRecords.length}
          unmatchedCount={state.rejectedRecords.length}
          fileStatus={state.fileStatus}
          language={state.language}
          theme={state.theme}
          onToggleLanguage={state.setLanguage}
          onToggleTheme={state.setTheme}
          onReloadLive={state.handleReload}
          onPageChange={state.setActivePage}
          onFileSelected={state.handleFileSelected}
        />

        <main className="main">
          {state.loadError ? (
            <div className="pageSub api-banner">
              <span>API error: {state.loadError}</span>
              <button type="button" className="inline-reload" onClick={state.handleReload}>
                {isEnglish ? "Retry" : "Thử lại"}
              </button>
            </div>
          ) : null}

          {state.activePage === "deals" ? (
            <DealsWorkspace
              filters={state.filters}
              kpis={state.kpis}
              groupedEntries={state.groupedEntries}
              flatRecords={state.flatRecords}
              locationOptions={state.locationOptions}
              metricsSummary={state.metricsSummary}
              language={state.language}
              view={state.view}
              expandedKeys={state.expandedKeys}
              flatSort={state.flatSort}
              compareKeys={state.compareKeys}
              onViewChange={state.setView}
              onFilterChange={state.handleFilterChange}
              onClearFilters={state.handleClearFilters}
              onToggleExpanded={state.toggleExpanded}
              onChangeFlatSort={state.changeFlatSort}
              onToggleCompare={state.toggleCompare}
              onOpenDetail={detail.openDetail}
            />
          ) : null}

          {state.activePage === "locations" ? (
            <AnalyticsView
              variant="locations"
              title={isEnglish ? "Location" : "Địa điểm"}
              subtitle={isEnglish ? "Grouped from live deal records." : "Tổng hợp từ các deal đang có trên hệ thống."}
              language={state.language}
              items={state.locationInsights}
              onSelectLocation={state.handleSelectLocation}
            />
          ) : null}

          {state.activePage === "senders" ? (
            <AnalyticsView
              variant="senders"
              title={isEnglish ? "Sender" : "Người gửi"}
              subtitle={
                isEnglish
                  ? "Who is sending the strongest hotel coverage and commission."
                  : "Nhung dau moi dang gui nhieu deal va commission tot nhat."
              }
              language={state.language}
              items={state.senderInsights}
            />
          ) : null}

          {state.activePage === "unmatched" ? (
            <UnmatchedView
              language={state.language}
              records={state.rejectedRecords}
              onOpenDetail={detail.openDetail}
            />
          ) : null}
        </main>
      </div>

      <CompareDrawer
        language={state.language}
        groups={state.compareGroups}
        onRemove={(key) => state.setCompareKeys((c) => c.filter((k) => k !== key))}
        onClear={() => state.setCompareKeys([])}
      />

      <DetailModal
        language={state.language}
        open={detail.open}
        record={detail.record}
        detail={detail.payload}
        loading={detail.loading}
        error={detail.error}
        onClose={detail.closeDetail}
      />

      <div className={`toast ${state.toastMessage ? "is-visible" : ""}`}>{state.toastMessage}</div>
    </>
  );
}
