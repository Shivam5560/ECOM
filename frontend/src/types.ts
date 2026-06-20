export type Category = "Audio" | "Carry" | "Desk" | "Home" | "Wear";

export type Product = {
  id: string;
  name: string;
  category: Category;
  description: string;
  price: number;
  accent: string;
  image: string;
  rating: number;
  inventory: string;
};

export type CartItem = {
  product: Product;
  quantity: number;
};
