import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import UserProductDetailModal from "../components/products/UserProductDetailModal";

export interface Product {
  product_id: number;
  category_id: number;

  title: string;  // Updated
  description?: string;
  price: number;
  size?: string;
  color?: string;
  thumbnail?: string;   // Updated
  stock_quantity: number;
  is_active: boolean;

  images?: string[];
}

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

export default function Products() {

    const [products, setProducts] = useState<Product[]>([]);
    const [cart, setCart] = useState<Cart | null>(null);
    const [isProductDetailModalOpen, setIsProductDetailModalOpen] = useState(false);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

    // Fetch Orders
    async function fetchProducts()
    {
        try
        {
            const productResponse = await axiosClient.get("/products/active");
            setProducts(productResponse.data);
        }
        catch (err)
        {
            console.error("Failed to fetch orders: ", err);
        }
    }

    async function fetchCart()
    {
        try
        {
            const response = await axiosClient.get("/cart");
            setCart(response.data);
        }
        catch(err)
        {
            console.error("Failed to fetch cart: ", err);
        }
    }

    useEffect(() => {
        fetchProducts();
    }, []);



    return (
        <>
        {/* Header */}
        <div className="flex flex-col justify-center items-center gap-4 p-5">

            {/* Right-side icons */}
            <div className="absolute right-5 top-5 flex items-center gap-6 text-2xl">
                <Link to="/account" className="hover:text-gray-600 transition">
                    <i className="fa-regular fa-user"></i>
                </Link>

                <Link to="/cart" className="hover:text-gray-600 transition">
                    <i className="fa-solid fa-bag-shopping"></i>
                </Link>
            </div>

            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            <nav className="flex gap-12">
                <Link to="/"><p className="text-base font-normal tracking-widest">EVENTS</p></Link>
                <Link to="/products?category=1"><p className="text-base font-normal tracking-widest">NEW ARRIVALS</p></Link>
                <Link to="/products?category=2"><p className="text-base font-normal tracking-widest">WOMEN</p></Link>
                <Link to="/products?category=3"><p className="text-base font-normal tracking-widest">MEN</p></Link>
                <Link to="/products?category=4"><p className="text-base font-normal tracking-widest">BRANDS</p></Link>
                <Link to="/products?category=5"><p className="text-base font-normal tracking-widest">ACCESSORIES</p></Link>
                <Link to="/products?category=6"><p className="text-base font-normal tracking-widest">JEWELERY</p></Link>
            </nav>
        </div>

        {/* Main */}
        <div className="flex gap-2 p-8">
            
            {/* Filter Section */}
            <div className="border flex flex-col p-10">
                <h2>Filter</h2>
            </div>

            {/* Products Grid */}
            <div className="grid grid-cols-4 gap-3">
                {products.map((product) => {
                    return (
                    <div onClick={() => {
                        setIsProductDetailModalOpen(true); 
                        setSelectedProduct(product);
                        }} key={product.product_id} className="border flex flex-col gap-2 h-auto hover:bg-gray-100 rounded-2xl p-2 cursor-pointer">
                        <img src={product.thumbnail} className="h-60 object-cover border rounded-2xl"/>
                        <div className="flex flex-col gap-1">
                            <p className="text-lg leading-tight tracking-wider">{product.title.toUpperCase()}</p>
                            <div>
                                <p className="tracking-wider text-gray-500">${product.price.toFixed(2)}</p>
                                <p className="tracking-wider text-gray-500">Size: {product.size}</p>
                            </div>
                        </div>
                    </div>
                    );
                })}
            </div>

        </div>

        <UserProductDetailModal 
            isOpen={isProductDetailModalOpen}
            product={selectedProduct}
            cart={cart}
            onClose={() => setIsProductDetailModalOpen(false)}/>

        </>
    );
}