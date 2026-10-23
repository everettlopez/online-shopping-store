import { Link, useLocation } from "react-router-dom";

interface ProductCardProps {
    product: {
        product_id: number;
        title: string;
        price: number;
        size?: string | null;
        thumbnail?: string | null;
    };
}

// Links to the product's own page, which uses `from` for its back link
export default function ProductCard({ product }: ProductCardProps) {
    const location = useLocation();

    return (
        <Link
            to={`/products/${product.product_id}`}
            state={{ from: location.pathname + location.search }}
            className="border flex flex-col gap-2 h-auto hover:bg-gray-100 rounded-2xl p-2 min-w-0"
        >
            <img src={product.thumbnail ?? undefined} alt={product.title} className="aspect-[4/5] w-full object-cover border rounded-2xl"/>
            <div className="flex flex-col gap-1 min-w-0">
                <p className="text-base md:text-lg leading-tight tracking-wider line-clamp-2 break-words">{product.title.toUpperCase()}</p>
                <div className="text-sm md:text-base">
                    <p className="tracking-wider text-gray-500">${product.price.toFixed(2)}</p>
                    {product.size && <p className="tracking-wider text-gray-500 truncate">Size: {product.size}</p>}
                </div>
            </div>
        </Link>
    );
}
