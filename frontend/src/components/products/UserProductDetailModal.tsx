import { useEffect, useState } from "react";
import axiosClient from "../../api/axiosClient";

import { useAuth } from "../../context/AuthContext";

type Product = {
    product_id: number;
    category_id: number;
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

interface CartItem {
    cart_item_id: number;
    product_id: number;
    quantity: number;
    product: Product | null;
}

interface Cart {
    cart_id: number;
    user_id: number;
    items: CartItem[];
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
  cart: Cart | null;
}


export default function ProductDetailModal({isOpen, onClose, product, cart}: Props) 
{
  if (!isOpen) return null;

  const [alreadyAdded, setAlreadyAdded] = useState(false);

  useEffect(() => {
    if (!cart || !product) return;

    let found = false;
    for (let i = 0; i < cart.items.length; i++) {
      if (cart.items[i].product_id === product.product_id) {
        found = true;
        break;
      }
    }

    console.log("manual found:", found);
    setAlreadyAdded(found);
  }, [cart, product]);

  async function handleAddToCart()
  {
    try 
    {
      const response = await axiosClient.post(`/cart/items?product_id=${product.product_id}`);


      console.log(response.data);
    }
    catch (err)
    {
      console.error("Failed to add product to cart: ", err);
    }
  }
  
  return (
    <>
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="flex bg-white gap-6 rounded-lg p-4">
        <img src={product?.thumbnail} className="border object-cover h-[400px] rounded-lg"/>

        <div className="flex flex-col w-[600px] p-2 gap-8">
          
          {/* Close Button */}
          <div className="w-full flex justify-end">
            <button onClick={onClose} className="px-4 py-2">CLOSE</button>
          </div>

          <div className="flex flex-col">
            <h1 className="text-4xl tracking-wide">{product?.title.toUpperCase()}</h1>
            <p className="text-gray-400 text-lg py-2">${product?.price.toFixed(2)}</p>
            <p className="text-lg">{product?.description}</p>
          </div>

          {/* Cart Button*/}
          <div className="flex h-full items-end justify-center p-2">
            {alreadyAdded ? (
              <><button disabled className="border px-5 py-1 rounded-full bg-gray-100">Added to Cart</button></>) : (<><button onClick={() => {handleAddToCart(); setAlreadyAdded(true);}} className="border px-5 py-1 rounded-full transition-all duration-1000 hover:bg-gray-100">Add to Cart</button></>)}
          </div>
        </div>
        
      </div>
    </div>
    </>
  );
}
