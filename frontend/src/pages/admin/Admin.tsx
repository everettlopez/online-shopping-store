import { useState } from "react";
import { useAuth } from "../../context/AuthContext";

import { Link } from "react-router-dom";

import ProductIcon from "../../assets/products-svgrepo-com.svg";

import CategoryIcon from "../../assets/tags-category-categories-labels-svgrepo-com.svg"
import UserIcon from "../../assets/users-svgrepo-com.svg";
import OrderIcon from "../../assets/orders-svgrepo-com.svg";

console.log("DEBUG: Admin page component loaded");


function Admin() {

    return (
        <>
        {/* Header */}
        <div className="relative flex flex-col justify-center items-center gap-4 p-5">

            {/* Logo */}
            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            {/* Navigation */}
            <nav className="flex gap-12">
                <Link to="/admin/products"><p className="text-base font-normal tracking-widest">PRODUCTS</p></Link>
                <Link to="/"><p className="text-base font-normal tracking-widest">CATEGORIES</p></Link>
                <Link to="/"><p className="text-base font-normal tracking-widest">USERS</p></Link>
                <Link to="/"><p className="text-base font-normal tracking-widest">ORDERS</p></Link>
            </nav>
        </div>

        {/* Admin Action Cards */}
        <div className="flex justify-center mt-16">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-6xl px-6">

                {/* Products */}
                <Link 
                    to="/admin/products"
                    className="flex flex-col items-center p-8 bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200"
                >
                    <img src={ProductIcon} alt="Product Icon" className="h-20 w-20"/>
                    <h2 className="text-xl font-semibold tracking-wide">PRODUCTS</h2>
                    <p className="text-gray-500 text-sm mt-2 text-center">Create & manage products</p>
                </Link>

                {/* Categories */}
                <Link 
                    to="/admin/categories"
                    className="flex flex-col items-center p-8 bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200"
                >
                    <img src={CategoryIcon} alt="Category Icon" className="h-20 w-20"/>
                    <h2 className="text-xl font-semibold tracking-wide">CATEGORIES</h2>
                    <p className="text-gray-500 text-sm mt-2 text-center">Organize product categories</p>
                </Link>

                {/* Users */}
                <Link 
                    to="/admin/users"
                    className="flex flex-col items-center p-8 bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200"
                >
                    <img src={UserIcon} alt="Users Icon" className="h-20 w-20"/>
                    <h2 className="text-xl font-semibold tracking-wide">USERS</h2>
                    <p className="text-gray-500 text-sm mt-2 text-center">View & manage users</p>
                </Link>

                {/* Orders */}
                <Link 
                    to="/admin/orders"
                    className="flex flex-col items-center p-8 bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200"
                >
                    <img src={OrderIcon} alt="Order Icon" className="h-20 w-20"/>
                    <h2 className="text-xl font-semibold tracking-wide">ORDERS</h2>
                    <p className="text-gray-500 text-sm mt-2 text-center">Track & update orders</p>
                </Link>

            </div>
        </div>

        </>
    );
}

export default Admin;