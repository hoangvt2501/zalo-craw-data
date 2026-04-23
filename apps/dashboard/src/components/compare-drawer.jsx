import { formatCompact, formatCurrency, getContact, getMaxPrice, getMinPrice } from "../lib/dashboard-utils";

export default function CompareDrawer({ language, groups, onRemove, onClear }) {
  const isEnglish = language === "en";

  if (!groups.length) {
    return <div className="cmp-bar" />;
  }

  const bestPrices = groups.map((group) => {
    const mins = group.offers.map(getMinPrice).filter(Boolean);
    return mins.length ? Math.min(...mins) : null;
  });
  const globalBest = Math.min(...bestPrices.filter(Boolean));

  const maxCommissions = groups.map((group) => Math.max(...group.offers.map((offer) => Number(offer.commission_vnd) || 0)));
  const globalMaxCom = Math.max(...maxCommissions);

  return (
    <div className={`cmp-bar ${groups.length ? "open" : ""}`}>
      <div className="cmp-bar-inner">
        <div className="cmp-header">
          <div className="cmp-title">{isEnglish ? "Compare groups" : "So sanh nhom"}</div>

          <div className="cmp-slots">
            {groups.map((group) => (
              <div key={group.key} className="cmp-slot">
                <span className="cmp-slot-name" title={group.offers[0]?.property_name || group.offers[0]?.hotel_name}>
                  {group.offers[0]?.property_name || group.offers[0]?.hotel_name}
                </span>
                <button type="button" className="cmp-slot-rm" onClick={() => onRemove(group.key)}>x</button>
              </div>
            ))}
            {groups.length < 3 ? <div className="cmp-slot empty">+ add hotel</div> : null}
          </div>

          <div className="cmp-actions">
            <button type="button" className="cmp-clear" onClick={onClear}>
              {isEnglish ? "Clear" : "Xoa"}
            </button>
          </div>
        </div>

        {groups.length >= 2 ? (
          <div className="cmp-table-wrap">
            <table className="cmp-table">
              <tbody>
                <tr>
                  <td className="row-label" />
                  {groups.map((group) => (
                    <td key={`${group.key}-head`} className="cmp-col">
                      <div className="cmp-hotel-name">{group.offers[0]?.hotel_name || "-"}</div>
                      <div className="cmp-hotel-loc">
                        {group.offers[0]?.location || "-"}
                        {group.offers[0]?.stars ? ` · ${group.offers[0].stars}*` : ""}
                      </div>
                      <div className="cmp-note">{group.offers.length} offers</div>
                    </td>
                  ))}
                </tr>

                <tr className="winner-row">
                  <td className="row-label">{isEnglish ? "Best price" : "Giá tốt nhất"}</td>
                  {bestPrices.map((price, index) => {
                    const isBest = price === globalBest;
                    const diff = price && globalBest ? Math.round(((price - globalBest) / globalBest) * 100) : 0;
                    return (
                      <td key={`${groups[index].key}-price`} className={`cmp-col ${isBest ? "winner" : price && price > globalBest ? "loser" : ""}`}>
                        <div className={`cmp-price-val ${isBest ? "best" : price && price > globalBest ? "worst" : ""}`}>{formatCurrency(price, language)}</div>
                        {isBest ? <div className="cmp-diff best">{isEnglish ? "best" : "tot nhat"}</div> : diff > 0 ? <div className="cmp-diff up">+{diff}%</div> : null}
                      </td>
                    );
                  })}
                </tr>

                <tr>
                  <td className="row-label">{isEnglish ? "Range" : "Dai gia"}</td>
                  {groups.map((group) => {
                    const low = Math.min(...group.offers.map((offer) => getMinPrice(offer) || Number.MAX_SAFE_INTEGER));
                    const high = Math.max(...group.offers.map((offer) => getMaxPrice(offer) || 0));
                    return (
                      <td key={`${group.key}-range`} className="cmp-col">
                        {high && high !== low ? `${formatCompact(low, language)} - ${formatCompact(high, language)}` : formatCompact(low, language)}
                      </td>
                    );
                  })}
                </tr>



                <tr>
                  <td className="row-label">{isEnglish ? "Offers" : "So offer"}</td>
                  {groups.map((group) => (
                    <td key={`${group.key}-offers`} className="cmp-col">{group.offers.length}</td>
                  ))}
                </tr>

                <tr>
                  <td className="row-label">{isEnglish ? "Breakfast" : "An sang"}</td>
                  {groups.map((group) => (
                    <td key={`${group.key}-breakfast`} className="cmp-col">
                      {group.offers.some((offer) => offer.includes_breakfast === true)
                        ? "yes"
                        : group.offers.every((offer) => offer.includes_breakfast === false)
                          ? "no"
                          : "-"}
                    </td>
                  ))}
                </tr>

                <tr>
                  <td className="row-label">{isEnglish ? "Dates" : "Ngay trong"}</td>
                  {groups.map((group) => (
                    <td key={`${group.key}-dates`} className="cmp-col">
                      {[...new Set(group.offers.flatMap((offer) => offer.checkin_dates || []))].slice(0, 5).join(", ") || "-"}
                    </td>
                  ))}
                </tr>

                <tr>
                  <td className="row-label">{isEnglish ? "Best contact" : "Lien he tot nhat"}</td>
                  {groups.map((group) => (
                    <td key={`${group.key}-contact`} className="cmp-col">
                      <div>{group.offers[0]?.sender_name || "-"}</div>
                      <div className="cmp-note">{getContact(group.offers[0] || {})}</div>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </div>
  );
}
