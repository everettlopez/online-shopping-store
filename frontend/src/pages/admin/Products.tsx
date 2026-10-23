import { useEffect, useMemo, useState } from "react";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import AdminProductEditModal from "../../components/admin/products/AdminProductEditModal";
import AdminNav from "../../components/admin/AdminNav";
import AdminSnackbar, { type AdminNotice } from "../../components/admin/AdminSnackbar";
import { getCategories, type Category } from "../../api/admin";
import { apiErrorMessage } from "../../api/errors";
import { createProduct, getAllProducts } from "../../api/products";
import { FormControlLabel, FormGroup, InputLabel, MenuItem, Select, TextField } from "@mui/material";
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import NumberField from "../../components/NumberField";
import SizeField from "../../components/admin/products/SizeField";
import ColorField from "../../components/admin/products/ColorField";
import Switch from '@mui/material/Switch';


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
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<ProductRead | null>(null);
  const [isProductDetailModalOpen, setIsProductDetailModalOpen] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [notice, setNotice] = useState<AdminNotice>(null);


  // Create Product Constants
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState(0);
  const [size, setSize] = useState("");
  const [color, setColor] = useState("");
  const [price, setPrice] = useState<number | null>(null);
  const [stock, setStock] = useState<number | null>(1);
  const [isActive, setIsActive] = useState(true);
  const [thumbnail, setThumbnail] = useState<File | null>(null);


  // Data grid columns
  const columns: GridColDef[] = [
    {field: "id", headerName: "Product ID", width: 100, resizable: false,},
    {field: "active", headerName: "Active", width: 100, resizable: false},
    {field: "category", headerName: "Category", width: 100, resizable: false,},
    {field: "thumbnail", headerName: "Thumbnail", width: 200, resizable: false, renderCell: (params) => (
      <img src={params.value} alt="" className="h-10 w-10 object-cover"/>
    ),},
    {field: "name", headerName: "Name", width: 300, resizable: false,},
    {field: "price", headerName: "Price ($)", width: 100, resizable: false,},
    {field: "size", headerName: "Size", width: 100, resizable: false},
    {field: "color", headerName: "Color", width: 120, resizable: false},
    // Sold-out products are hidden from the storefront until they're restocked
    {field: "stock", headerName: "Stock", width: 100, resizable: false, renderCell: ({ value }: { value?: number }) => (
      value && value > 0 ? value : <span className="text-red-600">Sold out</span>
    )},
    {field: "expand", headerName: "", width: 80, resizable: false, sortable: false, renderCell: (params) => (
      <button className="text-blue-600 underline"
        onClick={() => {
          const fullProduct = products.find(p => p.product_id === params.row.id);
          setSelectedProduct(fullProduct || null);
          setIsProductDetailModalOpen(true);
        }}>
          View
      </button>
    )},
  ];

  const rows = useMemo(() => products.map((product) => ({
    id: product.product_id,
    active: product.is_active,
    category: product.category.name,
    thumbnail: product.thumbnail,
    name: product.title,
    price: product.price.toFixed(2),
    size: product.size,
    color: product.color,
    stock: product.stock_quantity,
  })), [products]);
  const usedColors = useMemo(() => products.map((product) => product.color), [products]);

  async function fetchProducts()
  {
    try
    {
      setProducts(await getAllProducts());
    }
    catch (err)
    {
      setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to load products") });
    }
  }

  useEffect(() => {
    getAllProducts().then(setProducts, (err) => setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to load products") }));
    getCategories()
      .then(setCategories)
      .catch((err) => setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to load categories") }));

  }, []);

  async function handleCancelCreate()
  {
    try
    {
      setTitle("");
      setDescription("");
      setCategory(0);
      setSize("");
      setColor("");
      setPrice(null);
      setStock(1);
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
      formData.append("stock_quantity", String(stock));
      formData.append("is_active", String(isActive));

      if (thumbnail) {
        formData.append("thumbnail", thumbnail);
      }

      await createProduct(formData);

      setNotice({ severity: "success", message: "Product created" });
      fetchProducts(); // refresh grid
      handleCancelCreate();
    } catch (err) {
      setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to create new product") });
    }
  }



  return (
    <>
      <AdminNav />

            <div className="p-4 md:p-10">

        {/* Create Product */}
        <div className="flex flex-col gap-3">
          <h1 className="text-2xl md:text-4xl tracking-wider">CREATE NEW PRODUCT</h1>

          {/* The photo above the fields until 1024 px, beside them from there */}
          <div className="flex flex-col lg:flex-row gap-2 border p-2">

            {/* Add Thumbnail Div */}
            <div
              role="button"
              tabIndex={0}
              aria-label={thumbnail ? "Change thumbnail" : "Add thumbnail"}
              onClick={() => document.getElementById("thumbnail-input")?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  document.getElementById("thumbnail-input")?.click();
                }
              }}
              className="border flex flex-col border-gray-300 w-full h-48 lg:h-auto lg:w-80 shrink-0 rounded-xl items-center justify-center hover:bg-gray-100 transition-all duration-500 ease-in-out cursor-pointer">
              <input id="thumbnail-input" type="file" accept="image/*" className="hidden" onChange={(e) => {
                const file = e.target.files?.[0];
                if (file)
                {
                  setThumbnail(file);
                }
              }}/>
              {thumbnail ? (
                <img src={URL.createObjectURL(thumbnail)} alt="New thumbnail" className="h-full w-full object-cover rounded-lg"/>
              ) : (
                <>
                <AddCircleOutlinedIcon className="text-gray-300 h-20 w-20" />
                <p>Add Thumbnail</p>
                </>
              )}
            </div>

            <div className="border w-full min-w-0 rounded-lg p-2 flex flex-col gap-3">

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

              {/* Multiple Field Inputs: two to a row until 1280 px */}
              <div className="grid grid-cols-2 xl:flex xl:items-center gap-2">
                {/* Category Selection */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel required>Category</InputLabel>
                  <Select required value={category} defaultValue={0} onChange={(e) => setCategory(Number(e.target.value))}>
                    <MenuItem disabled value={0}>Select a Category</MenuItem>
                    {categories.map((c) => (
                      <MenuItem key={c.category_id} value={c.category_id}>{c.name}</MenuItem>
                    ))}
                  </Select>
                </FormGroup>

                {/* Size: a preset or anything typed */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel>Size</InputLabel>
                  <SizeField value={size} onChange={setSize}/>
                </FormGroup>

                {/* Color: a suggestion or anything typed */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel>Color</InputLabel>
                  <ColorField value={color} onChange={setColor} usedColors={usedColors}/>
                </FormGroup>

                {/* Price Wheel */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel required>Price</InputLabel>
                  <NumberField label="Price ($)" value={price} min={1} onValueChange={(newValue) => setPrice(newValue)}/>
                </FormGroup>

                {/* Stock Wheel */}
                <FormGroup className="flex flex-col gap-2">
                  <InputLabel required>Stock</InputLabel>
                  <NumberField label="Stock" value={stock} min={0} step={1} onValueChange={(newValue) => setStock(newValue)}/>
                </FormGroup>

                <FormGroup className="h-full flex justify-center items-center">
                  <FormControlLabel label="Active" control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)}/>}/>
                </FormGroup>              
              </div>

              {/* Cancel/Create Buttons */}
              <div className="border flex justify-between">
                <button className="border rounded-full px-5 py-1" onClick={() => handleCancelCreate()}>Cancel</button>
                <button disabled={!title || !price || stock === null || !category || !thumbnail} onClick={() => handleCreate()} className="border rounded-full px-5 py-1 disabled:bg-gray-100 disabled:text-gray-400">Create</button>
              </div>
            </div>
          </div>
        </div>

        {/* Product Table */}
        <div className="flex flex-col min-w-0">
          <h1 className="text-2xl md:text-4xl tracking-wider py-3">PRODUCTS</h1>
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
        categories={categories}
        usedColors={usedColors}
        onClose={() => {
          setIsProductDetailModalOpen(false);
          setSelectedProduct(null);
          fetchProducts();
        }}
      />

      <AdminSnackbar notice={notice} onClose={() => setNotice(null)} />
    </>
  );
}
