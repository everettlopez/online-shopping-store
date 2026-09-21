import { useEffect, useState } from "react";
import axiosClient from "../../api/axiosClient";
import { Link } from "react-router-dom";   // ← FIXED: Link imported
import { useAuth } from "../../context/AuthContext";
import { DataGrid } from "@mui/x-data-grid";
import AdminProductEditModal from "../../components/admin/products/AdminProductEditModal";
import { FormControlLabel, FormGroup, InputLabel, MenuItem, Select, TextField } from "@mui/material";
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import NumberField from "../../components/NumberField";
import Switch from '@mui/material/Switch';


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

export interface CategoryRead {
  category_id: number;
  name: string;
  description?: string | null;
}

export interface ProductRead {
  product_id: number;
  category: CategoryRead;
  title: string;
  description?: string | null;
  price: number;

  size?: string | null;
  color?: string | null;
  thumbnail?: string | null;

  stock_quantity: number;
  is_active: boolean;
  created_at: string;   // ISO datetime
  updated_at: string;   // ISO datetime
  images?: string[] | null;
}



export default function AdminProductsPage() {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [isProductDetailModalOpen, setIsProductDetailModalOpen] = useState(false);


  // Create Product Constants
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState(0);
  const [size, setSize] = useState("0");
  const [color, setColor] = useState("0");
  const [price, setPrice] = useState(null);
  const [isActive, setIsActive] = useState(true);
  const [thumbnail, setThumbnail] = useState<File | null>(null);


  // Data grid columns
  const columns = [
    {field: "id", headerName: "Product ID", width: 100, resizable: false,},
    {field: "active", headerName: "Active", width: 100, resizable: false},
    {field: "category", headerName: "Category", width: 100, resizable: false,},
    {field: "thumbnail", headerName: "Thumbnail", width: 200, resizable: false, renderCell: (params) => (
      <img src={params.value} alt="thumbnail" className="h-10 w-10 object-cover"/>
    ),},
    {field: "name", headerName: "Name", width: 300, resizable: false,},
    {field: "price", headerName: "Price ($)", width: 100, resizable: false,},
    {field: "size", headerName: "Size", width: 100, resizable: false},
    {field: "expand", headerName: "", width: 80, resizable: false, sortable: false, renderCell: (params: any) => (
      <button className="text-blue-600 underline"
        onClick={() => {
          const fullProduct = products.find(p => p.product_id === params.row.id);
          setExpandedRow(params.row.id);
          setSelectedProduct(fullProduct || null);
          setIsProductDetailModalOpen(true);
        }}>
          View
      </button>
    )},
  ];

  const [rows, setRows] = useState([]);

  async function fetchProducts()
  {
    try
    {
      const response = await axiosClient.get("/products");
      setProducts(response.data);

      const formatted = response.data.map((product: ProductRead) => ({
        id: product.product_id,
        active: product.is_active,
        category: product.category.name,
        thumbnail: product.thumbnail,
        name: product.title,
        price: product.price.toFixed(2),
        size: product.size,
      }));

      setRows(formatted);
    }
    catch (err)
    {
      console.error("Failed to load products: ", err);
    }
  }

  useEffect(() => {
    fetchProducts();

  }, []);

  async function handleCancelCreate()
  {
    try
    {
      setTitle("");
      setDescription("");
      setCategory(0);
      setSize("0");
      setColor("0");
      setPrice(null);
      setIsActive(true);
      setThumbnail(null);
    }
    catch(err)
    {
      console.error("Failed to cancel create product", err);
    }
  }

  async function handleCreate() {
    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("description", description);
      formData.append("category_id", String(category));
      formData.append("size", size);
      formData.append("color", color);
      formData.append("price", String(price));
      formData.append("is_active", String(isActive));

      if (thumbnail) {
        formData.append("thumbnail", thumbnail);
      }

      const response = await axiosClient.post("/products", formData);

      console.log("Created product:", response.data);
      fetchProducts(); // refresh grid
      handleCancelCreate();
    } catch (err) {
      console.error("Failed to create new product:", err);
    }
  }

  const eligibleProduct = title && price && category;


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

      <div className="p-10">

        {/* Create Product */}
        <div className="flex flex-col gap-3">
          <h1 className="text-4xl tracking-wider">CREATE NEW PRODUCT</h1>
          
          <div className="flex gap-2 border p-2">

            {/* Add Thumbnail Div */}
            <div
              onClick={() => document.getElementById("thumbnail-input")?.click()} 
              className="border flex flex-col border-gray-300 w-80 rounded-xl items-center justify-center hover:bg-gray-100 transition-all duration-500 ease-in-out cursor-pointer">
              <input id="thumbnail-input" type="file" accept="image/*" className="hidden" onChange={(e) => {
                const file = e.target.files?.[0];
                if (file)
                {
                  setThumbnail(file);
                }
              }}/>
              {thumbnail ? (
                <img src={URL.createObjectURL(thumbnail)} className="h-full w-full object-cover rounded-lg"/>
              ) : (
                <>
                <AddCircleOutlinedIcon className="text-gray-300 h-20 w-20" />
                <p>Add Thumbnail</p>
                </>
              )}
            </div>

            <div className="border w-full rounded-lg p-2 flex flex-col gap-3">

              {/* Title */}
              <FormGroup className="flex flex-col gap-2">
                <InputLabel id="create-product-title-label">Product Title</InputLabel>
                <TextField id="create-product-title-text" required label="Title" value={title} onChange={(e) => setTitle(e.target.value)}/>
              </FormGroup>

              {/* Description */}
              <FormGroup className="flex flex-col gap-2">
                <InputLabel>Product Description</InputLabel>
                <TextField multiline minRows={1} maxRows={2} label="Description" value={description} onChange={(e) => setDescription(e.target.value)}/>
              </FormGroup>

              {/* Multiple Field Inputs */}
              <div className="flex items-center gap-2">
                {/* Category Selection */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel required>Category</InputLabel>
                  <Select required value={category} defaultValue={0} onChange={(e) => setCategory(e.target.value)}>
                    <MenuItem disabled value={0}>Select a Category</MenuItem>
                    <MenuItem value={1}>New Arrivals</MenuItem>
                    <MenuItem value={2}>Women</MenuItem>
                    <MenuItem value={3}>Men</MenuItem>
                    <MenuItem value={4}>Brands</MenuItem>
                    <MenuItem value={5}>Accessories</MenuItem>
                    <MenuItem value={6}>Jewlery</MenuItem>
                  </Select>
                </FormGroup>

                {/* Size Selection */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel>Size</InputLabel>
                  <Select value={size} defaultValue="0" onChange={(e) => setSize(e.target.value)}>
                    <MenuItem disabled value="0">Select a size</MenuItem>
                    <MenuItem value="1SZ">1SZ</MenuItem>
                    <MenuItem value="XS">XS</MenuItem>
                  </Select>
                </FormGroup>

                {/* Color Selection */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel>Color</InputLabel>
                  <Select value={color} defaultValue="0" onChange={(e) => setColor(e.target.value)}>
                    <MenuItem disabled value="0">Select a color</MenuItem>
                    <MenuItem value="black">Black</MenuItem>
                    <MenuItem value="blue">Blue</MenuItem>
                  </Select>
                </FormGroup>

                {/* Price Wheel */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel required>Price</InputLabel>
                  <NumberField label="Price ($)" value={price} min={1} onValueChange={(newValue) => setPrice(newValue)}/>  
                </FormGroup>

                <FormGroup className="h-full flex justify-center items-center">
                  <FormControlLabel label="Acive" control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)}/>}/>
                </FormGroup>              
              </div>

              {/* Cancel/Create Buttons */}
              <div className="border flex justify-between">
                <button className="border rounded-full px-5 py-1" onClick={() => handleCancelCreate()}>Cancel</button>
                <button disabled={!title || !price || !category || !thumbnail} onClick={() => handleCreate()} className="border rounded-full px-5 py-1 disabled:bg-gray-100 disabled:text-gray-400">Create</button>
              </div>
            </div>
          </div>
        </div>

        {/* Product Table */}
        <div className="flex flex-col">
          <h1 className="text-4xl tracking-wider py-3">PRODUCTS</h1>
          <DataGrid 
          rows={rows}
          columns={columns}
          checkboxSelection
          sx={{
          "& .MuiDataGrid-cell": {
                padding: "0 8px",        // remove giant padding
                lineHeight: "1.2rem",    // shrink row height
                display: "flex",
                alignItems: "center",
              }
          }}/>
        </div>
      </div>

      <AdminProductEditModal
        isOpen={isProductDetailModalOpen}
        product={selectedProduct}
        onClose={() => {
          setIsProductDetailModalOpen(false);
          setExpandedRow(null);
          setSelectedProduct(null);
          fetchProducts();
        }}
      />
    </>
  );
}
