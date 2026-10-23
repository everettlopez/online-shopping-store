// This file should have been AdminProductModal
import { useState } from "react";
import TextField from '@mui/material/TextField';
import NumberField from "../../NumberField";
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import { InputLabel, MenuItem, Select } from '@mui/material';

import ConfirmDeleteModal from "../ConfirmDeleteModal";
import SizeField from "./SizeField";
import ColorField from "./ColorField";
import AdminSnackbar, { type AdminNotice } from "../AdminSnackbar";
import { type Category } from "../../../api/admin";
import { apiErrorMessage } from "../../../api/errors";
import { deleteProduct, updateProduct } from "../../../api/products";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: ProductRead | null;
  categories: Category[];
  usedColors: (string | null | undefined)[];
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

// Mounted only while open, and again whenever the product changes (another product, or
// the saved version after an update), so the form always starts from the product
export default function ProductModal(props: Props) {
  if (!props.isOpen) return null;
  const { product } = props;
  return <ProductForm key={product ? `${product.product_id}-${product.updated_at}` : "none"} {...props} />;
}

function ProductForm({ onClose, product, categories, usedColors }: Props) {

  // Edit Product Constants, prefilled from the product
  const [title, setTitle] = useState(product?.title ?? "");
  const [description, setDescription] = useState(product?.description || "");
  const [category, setCategory] = useState<number | "">(product?.category.category_id ?? "");

  const [size, setSize] = useState(product?.size || "");
  const [color, setColor] = useState(product?.color || "");
  const [price, setPrice] = useState(product?.price ?? 0);
  const [stock, setStock] = useState(product?.stock_quantity ?? 0);
  const [isActive, setIsActive] = useState(product?.is_active ?? true);
  const [changes, setChanges] = useState(false);

  const [notice, setNotice] = useState<AdminNotice>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  async function confirmDeleteProduct()
  {
    if (!product) return;

    try
    {
      await deleteProduct(product.product_id);
      setDeleteModalOpen(false);
      onClose();
    }
    catch (err)
    {
      setDeleteModalOpen(false);
      setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to delete the product") });
    }
  }

  // SUBMIT HANDLER
  async function handleSubmit() {
    if (!product) return;

    try {
      const fd = new FormData();

      fd.append("title", title);
      fd.append("description", description);
      fd.append("category_id", String(category));
      fd.append("size", size);
      fd.append("color", color);
      fd.append("price", String(price));
      fd.append("stock_quantity", String(stock));
      fd.append("is_active", String(isActive));

      // Thumbnail is a string URL in your current setup
      fd.append("thumbnail", product.thumbnail ?? "");

      await updateProduct(product.product_id, fd);

      setChanges(false);
      setNotice({ severity: "success", message: "Updated the product" });
    } catch (err) {
      setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to submit changes to product") });
    }
  }



  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="flex flex-col bg-white p-8 rounded-lg shadow-xl justify-center items-center gap-5 w-[1000px]">

        {/* Title and Close */}
        <div className="flex justify-between w-full items-center">
          <div className="px-6"/>
          <h1 className="text-4xl">EDIT PRODUCT</h1>
          <button onClick={onClose} className="border">Close</button>
        </div>

        {/* Thumbnail and Form Row */}
        <div className="flex gap-4  w-full">

          {/* Thumbnail */}
          <img src={product?.thumbnail ?? undefined} className="h-80 object-cover"/>

          {/* Form */}
          <div className="flex flex-col w-full gap-3">

            {/* Title */}
            <TextField required label="Title" value={title} onChange={(e) => {
              setTitle(e.target.value);
              setChanges(true);
            }}/>
            <TextField multiline label="Description" value={description} required onChange={(e) => {
              setDescription(e.target.value);
              setChanges(true);
            }}/>

            <div className="flex gap-2 items-center">
              {/* Category */}
              <FormGroup>
                <InputLabel required>Category</InputLabel>
                <Select value={category} onChange={(e) => {setCategory(Number(e.target.value)); setChanges(true);}}>
                  {categories.map((category) => {
                    return (
                      <MenuItem key={category.category_id} value={category.category_id}>{category.name}</MenuItem>
                    );
                  })}
                </Select>
              </FormGroup>

              <FormGroup>
                <InputLabel>Size</InputLabel>
                <SizeField value={size} onChange={(newValue) => {setSize(newValue); setChanges(true);}}/>
              </FormGroup>

              <FormGroup>
                <InputLabel>Color</InputLabel>
                <ColorField value={color} usedColors={usedColors} onChange={(newValue) => {setColor(newValue); setChanges(true);}}/>
              </FormGroup>

              <FormGroup className="w-40">
                <InputLabel required>Price</InputLabel>
                <NumberField value={price} min={1} onValueChange={(newValue) => {setPrice(newValue ?? 0); setChanges(true);}}/>
              </FormGroup>

              <FormGroup className="w-32">
                <InputLabel required>Stock</InputLabel>
                <NumberField value={stock} min={0} step={1} onValueChange={(newValue) => {setStock(newValue ?? 0); setChanges(true);}}/>
              </FormGroup>

              <FormGroup>
                <FormControlLabel label="Active" control={<Switch checked={isActive} onChange={(e) => {setIsActive(e.target.checked); setChanges(true);}}/>}/>
              </FormGroup>
            </div>
          </div>
        </div>

        <div className="w-full flex justify-between">
          <button onClick={() => setDeleteModalOpen(true)} className="border px-5 py-1 rounded-full">Delete</button>
          <button disabled={!changes} onClick={() => {handleSubmit();}} className="transition-all duration-1000 border px-5 py-1 rounded-full disabled:bg-gray-100 disabled:text-gray-400">Update</button>
        </div>
      </div>

      <ConfirmDeleteModal
        open={deleteModalOpen}
        message="Are you sure you want to delete this product?"
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDeleteProduct}/>

      <AdminSnackbar notice={notice} onClose={() => setNotice(null)} />

    </div>
  );


}
