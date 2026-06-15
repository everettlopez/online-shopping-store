import axiosClient from "./axiosClient";

export interface RegisterData {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
}

export interface LoginData {
    email: string;
    password: string;
}

// Register a new user to the database
export const register = async (data: RegisterData) => {
    const response = await axiosClient.post("/auth/register", data);
    return response.data;
};

// Login and retrieve the Cookie-based JWT token
export const login = async (data: LoginData) => {
    const response = await axiosClient.post("/auth/login", data);
    return response.data;
};

// Logout a user (delete cookie)
export const logout = async() => {
    const response = await axiosClient.post("/auth/logout");
    return response.data;
};

export const getCurrentUser = async() => {
    const response = await axiosClient.get("/auth/me");
    return response.data;
};

export const deleteAccount = async() => {
    const response = await axiosClient.delete("/auth/me");
    return response.data;
};

export const updateEmail = async(newEmail: string) => {
    const response = await axiosClient.put("/auth/me/email", {
        new_email: newEmail,
    });

    return response.data;
};

export const updatePassword = async(oldPassword: string, newPassword: string) => {
    const response = await axiosClient.put("/auth/me/password", {
        old_password: oldPassword, new_password: newPassword,
    });

    return response.data;
};