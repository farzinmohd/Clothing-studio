import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from orders.models import OrderItem
from products.models import Product

def get_collaborative_recommendations(product_id, top_n=4):
    """
    Returns a list of Product objects similar to the given product_id
    based on 'Item-Item Collaborative Filtering'.
    Logic: "Users who bought this also bought..."
    """
    try:
        # 1. Fetch Order Data
        # We need (user_id, product_id, quantity)
        order_items = OrderItem.objects.select_related('order__user').values(
            'order__user_id', 'product_id', 'quantity'
        )

        if not order_items:
            return []

        # 2. Create DataFrame
        df = pd.DataFrame(list(order_items))

        # Check if we have enough data (at least multiple users and products)
        if df['order__user_id'].nunique() < 2 or df['product_id'].nunique() < 2:
            return []

        # 3. Create Pivot Table (User-Item Matrix)
        # Rows: Users, Columns: Products, Values: Quantity
        user_item_matrix = df.pivot_table(
            index='order__user_id', 
            columns='product_id', 
            values='quantity', 
            fill_value=0
        )

        # 4. Calculate Item-Item Similarity
        # We transpose because we want similarity between Columns (Products), not Rows (Users)
        item_item_matrix = user_item_matrix.T
        similarity_matrix = cosine_similarity(item_item_matrix)

        # Create a DataFrame for easy lookup
        similarity_df = pd.DataFrame(
            similarity_matrix,
            index=item_item_matrix.index,
            columns=item_item_matrix.index
        )

        # 5. Get similarities for the target product
        if product_id not in similarity_df.index:
            return []

        # Sort by similarity score (descending)
        # Drop the product itself (similarity 1.0)
        similar_score_series = similarity_df[product_id].sort_values(ascending=False)
        similar_score_series = similar_score_series.drop(product_id)

        # Get top N product IDs
        top_product_ids = similar_score_series.head(top_n).index.tolist()

        # 6. Fetch actual Product objects
        # Preserve order of recommendation
        recommended_products = []
        for pid in top_product_ids:
            try:
                recommended_products.append(Product.objects.get(id=pid))
            except Product.DoesNotExist:
                continue

        return recommended_products

    except Exception as e:
        print(f"Collaborative Filtering Error: {e}")
        return []
