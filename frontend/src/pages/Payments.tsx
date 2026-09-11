import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements
} from "@stripe/react-stripe-js";

const stripePromise = loadStripe("");

function PaymentForm() {
  const stripe = useStripe();
  const elements = useElements();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();

    if (!stripe || !elements) return;

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: "http://localhost:5173/order-success"
      }
    });

    if (error) {
      console.error(error);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      <button>Pay Now</button>
    </form>
  );
}

export default function Payments() {
  const location = useLocation();
  const { clientSecret } = location.state || {};

  if (!clientSecret) {
    return <p>No client secret found</p>;
  }

  return (
    <Elements stripe={stripePromise} options={{ clientSecret }}>
      <PaymentForm />
    </Elements>
  );
}
