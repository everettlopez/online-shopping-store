import { useLocation } from "react-router-dom";

export default function Payments() {
  const location = useLocation();
  const { checkoutUrl } = location.state || {};

  if (!checkoutUrl) {
    return <p>No checkout URL found</p>;
  }

  window.location.href = checkoutUrl;
  return null;
}
