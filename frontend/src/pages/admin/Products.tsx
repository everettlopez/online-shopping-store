import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";   // ← FIXED: Link imported
import AddIcon from "../../assets/add-svgrepo-com.svg";
import { useAuth } from "../../context/AuthContext";
import ProductModal from "../../components/ProductModal";


export interface Product {
  product_id: number;
  category_id: number;
  name: string;
  description?: string;
  price: number;
  size?: string;
  color?: string;
  image_url?: string;
  stock_quantity: number;
  is_active: boolean;
}

export default function AdminProductsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  const [metadata, setMetadata] = useState<{ count: number; sort?: string | null }>({
        count: 0,
        sort: null
    });

  function openCreateModal() {
    setSelectedProduct(null);
    setIsModalOpen(true);
  }

  function openEditModal(product: Product) {
    setSelectedProduct(product);
    setIsModalOpen(true);
  }


  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/products");
        const data = await res.json();
        setProducts(data.products);
        setMetadata(data.metadata);
      } catch (err) {
        console.error("Failed to load products", err);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  if (loading) return <p>Loading products...</p>;

  return (
    <>
      {/* Header */}
      <div className="relative flex flex-col justify-center items-center gap-4 p-5">
        <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

        <nav className="flex gap-12">
          <Link to="/admin/products">
            <p className="text-base font-normal tracking-widest">PRODUCTS</p>
          </Link>
          <Link to="/admin/categories">
            <p className="text-base font-normal tracking-widest">CATEGORIES</p>
          </Link>
          <Link to="/admin/users">
            <p className="text-base font-normal tracking-widest">USERS</p>
          </Link>
          <Link to="/admin/orders">
            <p className="text-base font-normal tracking-widest">ORDERS</p>
          </Link>
        </nav>
      </div>

      <div className="flex text-center justify-center text-lg tracking-wider text-gray-400 border py-4">{metadata.count} PRODUCTS</div>


      {/* Product Grid */}
      <div className="p-10">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">

          {/* CREATE NEW PRODUCT CARD */}
          <div
            onClick={openCreateModal}

            className="border p-4 rounded-lg shadow flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 transition"
          >
            <img src={AddIcon} alt="Add icon" className="h-10 w-10 mb-3" />
            <p className="text-lg font-medium">Create New Product</p>
          </div>

          {/* EXISTING PRODUCTS */}
          {products.map((p) => (
            <div key={p.product_id} className="border p-4 rounded-lg shadow">
              <img
                src={p.image_url}
                alt={p.name}
                className="w-full h-48 object-cover rounded"
              />

              <h3 className="mt-4 text-lg font-semibold">{p.name}</h3>
              <p className="text-gray-600">${p.price}</p>
              <p className="text-sm text-gray-500">Size: {p.size}</p>
              <p className="text-sm text-gray-500">Color: {p.color}</p>

              <button
                onClick={() => openEditModal(p)}

                className="mt-4 w-full bg-blue-600 text-white py-2 rounded-full text-sm tracking-wide 
                           transition-all duration-200 hover:bg-blue-700"
              >
                Edit Product
              </button>
            </div>
          ))}
        </div>
      </div>

    <ProductModal
      isOpen={isModalOpen}
      onClose={() => setIsModalOpen(false)}
      product={selectedProduct}
    />

    </>
  );
}
