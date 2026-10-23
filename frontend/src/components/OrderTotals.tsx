// What an order cost: subtotal (items) + shipping + tax = total. Orders placed before
// shipping and tax were charged may have no breakdown, so only the total shows.
export type OrderAmounts = {
  total_amount: number;
  subtotal_amount?: number | null;
  shipping_amount?: number | null;
  tax_amount?: number | null;
  // What's been given back so far; 0 when nothing has
  refunded_amount?: number | null;
};

function Row({ label, amount, bold = false }: { label: string; amount: string; bold?: boolean }) {
  return (
    <div className={`flex justify-between ${bold ? "text-lg" : "text-gray-600"}`}>
      <p>{label}</p>
      <p>{amount}</p>
    </div>
  );
}

export default function OrderTotals({ order }: { order: OrderAmounts }) {
  const hasBreakdown = order.subtotal_amount != null;

  return (
    <div className="flex flex-col gap-1 w-full">
      {hasBreakdown && (
        <>
          <Row label="Subtotal" amount={`$${order.subtotal_amount!.toFixed(2)}`} />
          <Row label="Shipping" amount={order.shipping_amount ? `$${order.shipping_amount.toFixed(2)}` : "Free"} />
          <Row label="Tax" amount={`$${(order.tax_amount ?? 0).toFixed(2)}`} />
        </>
      )}
      <Row label="Total" amount={`$${order.total_amount.toFixed(2)}`} bold />
      {!!order.refunded_amount && (
        <Row label="Refunded" amount={`-$${order.refunded_amount.toFixed(2)}`} />
      )}
    </div>
  );
}
