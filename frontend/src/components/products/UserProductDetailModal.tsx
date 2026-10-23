import { useState } from "react";
import { Link } from "react-router-dom";
import { cartErrorMessage, useCart } from "../../context/CartContext";


type Product = {
    product_id: number;
    category: { category_id: number; name: string };
    title: string;
    description?: string;
    price: number;
    size?: string;
    color?: string;
    thumbnail?: string;
    images?: string[];
    stock_quantity: number;
    is_active: boolean;
};

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}


export default function ProductDetailModal({isOpen, onClose, product}: Props)
{
  const { items, add } = useCart();
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  // The error belongs to the product it was shown for
  const [errorFor, setErrorFor] = useState<number | null>(null);

  if (!isOpen || !product) return null;

  const inCart = items.find((line) => line.product_id === product.product_id)?.quantity ?? 0;
  const shownError = errorFor === product.product_id ? error : "";

  async function handleAddToCart()
  {
    if (!product) return;
    setAdding(true);
    setError("");

    try
    {
      await add(product);
    }
    catch (err)
    {
      setError(cartErrorMessage(err, "We couldn't add this to your cart. Please try again."));
      setErrorFor(product.product_id);
    }
    finally
    {
      setAdding(false);
    }
  }

  return (
    <>
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="flex bg-white gap-6 rounded-lg p-4">
        <img src={product.thumbnail} className="border object-cover h-[400px] rounded-lg"/>

        <div className="flex flex-col w-[600px] p-2 gap-8">

          {/* Close Button */}
          <div className="w-full flex justify-end">
            <button onClick={onClose} className="px-4 py-2">CLOSE</button>
          </div>

          <div className="flex flex-col">
            <h1 className="text-4xl tracking-wide">{product.title.toUpperCase()}</h1>
            <p className="text-gray-400 text-lg py-2">${product.price.toFixed(2)}</p>
            <p className="text-lg">{product.description}</p>
          </div>

          {/* Cart Button*/}
          <div className="flex flex-col h-full items-center justify-end gap-2 p-2">
            <button
              onClick={handleAddToCart}
              disabled={adding}
              className="border px-5 py-1 rounded-full transition-all duration-1000 hover:bg-gray-100 disabled:opacity-50">
                {adding ? "Adding..." : "Add to Cart"}
            </button>
            {inCart > 0 && (
              <p className="text-sm text-gray-500">
                {inCart} in your cart · <Link to="/cart" className="underline">View cart</Link>
              </p>
            )}
            {shownError && <p className="text-sm text-red-600">{shownError}</p>}
          </div>
        </div>

      </div>
    </div>
    </>
  );
}
