export type Category = string;

export type Product = {
  id: string;
  name: string;
  category: Category;
  description: string;
  price: number;
  accent: string;
  image: string;
  rating: number;
  stock: number;
};

export type CartItem = {
  product: Product;
  quantity: number;
};
