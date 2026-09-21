// This file should have been AdminProductModal
import * as React from 'react';
import { useState, useEffect } from "react";
import TextField from '@mui/material/TextField';
import NumberField from "../../NumberField";
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import { InputLabel, MenuItem, Select } from '@mui/material';
import axiosClient from "../../../api/axiosClient";

import ConfirmAdminProductDeleteModal from "../../../components/admin/products/ConfirmAdminProductDeleteModal";

import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: ProductRead | null;
}

type Category = {
  category_id: number;
  name: string;
  description?: string | null;
};

export interface CategoryRead {
  category_id: number;
  name: string;
  description?: string | null;
}

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

export default function ProductModal({ isOpen, onClose, product }: Props) {

  if (!isOpen)
  {
    console.log("PRODUCT MODAL CLOSED: ", isOpen);
    return null;
  }

  const [mainImage, setMainImage] = useState(product?.thumbnail);
  const [categories, setCategories] = useState<Category[]>([]);

  // Edit Product Constants
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState(product?.category.category_id ?? "");

  const [size, setSize] = useState("0");
  const [color, setColor] = useState("0");
  const [price, setPrice] = useState(0);
  const [isActive, setIsActive] = useState(true);
  const [thumbnail, setThumbnail] = useState<File | null>(null);
  const [changes, setChanges] = useState(false);

  const [alertOpen, setAlertOpen] = useState(false);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  function openDeleteModal() {
    setDeleteModalOpen(true);
  }

  function closeDeleteModal() {
    setDeleteModalOpen(false);
  }

  async function confirmDeleteOrder() 
  {
    try
    {
      await axiosClient.delete(`/products/${product?.product_id}`);
      console.log("Product deleted!")
      closeDeleteModal();
      onClose();
    }
    catch (err)
    {
      console.error("Failed to delete the order: ", err);
    }
  }




  const handleAlertClose = (event?: React.SyntheticEvent | Event, reason?: "timeout" | "clickaway",) => {
    if (reason === "clickaway")
    {
      return;
    }

    setAlertOpen(false);
  };

  useEffect(() => {
    if(product)
    {
      setMainImage(product.thumbnail);
    }
  }, [product]);


  useEffect(() => {
    async function loadCategories() {
      const res = await fetch("http://127.0.0.1:8000/api/categories", {
        credentials: "include",
      });

      if (!res.ok) return;

      const data = await res.json();
      setCategories(data.categories as Category[]);
    }

    loadCategories();
  }, []);

  // PREFILL WHEN EDITING
  useEffect(() => {
    if (!isOpen || !product) return;

    setTitle(product.title);
    setDescription(product.description || "");
    setCategory(product.category.category_id);
    setSize(product.size || "");
    setColor(product.color || "");
    setPrice(product.price);
    setIsActive(product.is_active);
    setThumbnail(product.thumbnail);

  }, [isOpen, product]);


  useEffect(() => {
    if (!product || !product.category.category_id) return;
    const fetchCategory = async () => {
      try 
      {
        const res = await axiosClient.get(`/categories/${product.category.category_id}`);
        const categoryData = res.data;
        setCategory(categoryData.category_id);

        console.log(res.data);
      }
      catch (err)
      {
        console.error("Failed to load product category: ", err);
      }
    };

    fetchCategory();

  }, [product?.category.category_id]);

  async function refreshEdit() {
    if (!product) return;

    try {
      const res = await axiosClient.get(`/products/${product.product_id}`);
      const updated = res.data;

      // Update REAL state, not form
      setTitle(updated.title);
      setDescription(updated.description || "");
      setCategory(updated.category.category_id);
      setSize(updated.size || "");
      setColor(updated.color || "");
      setPrice(updated.price);
      setIsActive(updated.is_active);
      setThumbnail(updated.thumbnail || "");

    } catch (err) {
      console.error("Failed to refresh edit form:", err);
    }
  }



  // SUBMIT HANDLER
  async function handleSubmit() {
    try {
      const fd = new FormData();

      fd.append("title", title);
      fd.append("description", description);
      fd.append("category_id", String(category));
      fd.append("size", size);
      fd.append("color", color);
      fd.append("price", String(price));
      fd.append("is_active", String(isActive));

      // Thumbnail is a string URL in your current setup
      fd.append("thumbnail", product?.thumbnail ?? "");

      const response = await axiosClient.put(`/products/${product?.product_id}`, fd);
      console.log("Updated product: ", response.data);

      setAlertOpen(true);

      refreshEdit();
    } catch (err) {
      console.error("Failed to submit changes to product:", err);
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
          <img src={product?.thumbnail} className="h-80 object-cover"/>

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
                <Select value={category} onChange={(e) => {setCategory(e.target.value); setChanges(true);}}>
                  {categories.map((category) => {
                    return (
                      <MenuItem key={category.category_id} value={category.category_id}>{category.name}</MenuItem>
                    );
                  })}
                </Select>
              </FormGroup>

              <FormGroup>
                <InputLabel>Size</InputLabel>
                <Select value={size} onChange={(e) => {setSize(e.target.value); setChanges(true);}}>
                  <MenuItem value="1SZ">1 Size</MenuItem>
                  <MenuItem value="XS">X-Small</MenuItem>
                  <MenuItem value="S">Small</MenuItem>
                  <MenuItem value="M">Medium</MenuItem>
                  <MenuItem value="L">Large</MenuItem>
                  <MenuItem value="XL">X-Large</MenuItem>
                </Select>
              </FormGroup>

              <FormGroup className="w-40">
                <InputLabel>Color</InputLabel>
                <TextField value={color} onChange={(e) => {setColor(e.target.value); setChanges(true);}}/>
              </FormGroup>

              <FormGroup className="w-40">
                <InputLabel required>Price</InputLabel>
                <NumberField value={price}/>
              </FormGroup>
              
              <FormGroup>
                <FormControlLabel label="Acive" control={<Switch checked={isActive} onChange={(e) => {setIsActive(e.target.checked); setChanges(true);}}/>}/>
              </FormGroup>

              <Snackbar
                open={alertOpen}
                autoHideDuration={3000}
                anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
              >
                <Alert
                  onClose={handleAlertClose}
                  severity="success"
                  variant="filled"
                  sx={{ width: "100%" }}
                >
                  Updated the product
                </Alert>
              </Snackbar>
            </div>
          </div>
        </div>

        <div className="w-full flex justify-between">
          <button onClick={() => openDeleteModal()} className="border px-5 py-1 rounded-full">Delete</button>
          <button disabled={!changes} onClick={() => {handleSubmit();}} className="transition-all duration-1000 border px-5 py-1 rounded-full disabled:bg-gray-100 disabled:text-gray-400">Update</button>
        </div>
      </div>

      <ConfirmAdminProductDeleteModal 
        isOpen={deleteModalOpen}
        onClose={closeDeleteModal}
        onConfirm={confirmDeleteOrder}/>

    </div>
  );


}
