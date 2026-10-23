interface ProductCardProps {
    product: {
        title: string;
        price: number;
        size?: string | null;
        thumbnail?: string | null;
    };
    onClick: () => void;
}

export default function ProductCard({ product, onClick }: ProductCardProps) {
    return (
        <div onClick={onClick} className="border flex flex-col gap-2 h-auto hover:bg-gray-100 rounded-2xl p-2 cursor-pointer">
            <img src={product.thumbnail ?? undefined} alt={product.title} className="h-60 w-full object-cover border rounded-2xl"/>
            <div className="flex flex-col gap-1">
                <p className="text-lg leading-tight tracking-wider">{product.title.toUpperCase()}</p>
                <div>
                    <p className="tracking-wider text-gray-500">${product.price.toFixed(2)}</p>
                    {product.size && <p className="tracking-wider text-gray-500">Size: {product.size}</p>}
                </div>
            </div>
        </div>
    );
}
