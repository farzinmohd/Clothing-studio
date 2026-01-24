import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings')
django.setup()

from ai_features.models import FAQ

def seed_faqs():
    sample_faqs = [
        {
            "question": "What is your return policy?",
            "answer": "You can return any unworn and unwashed item within 30 days of purchase. Simply visit our Returns Center to start your request.",
            "category": "Returns"
        },
        {
            "question": "How long does shipping take?",
            "answer": "Standard shipping usually takes 3-5 business days. Express shipping is available for 1-2 business day delivery.",
            "category": "Shipping"
        },
        {
            "question": "Do you offer international shipping?",
            "answer": "Yes, we ship to over 50 countries worldwide! Shipping costs and times vary by location.",
            "category": "Shipping"
        },
        {
            "question": "How can I track my order?",
            "answer": "Once your order ships, you'll receive an email with a tracking link. You can also track it in the 'Orders' section of your profile.",
            "category": "Orders"
        },
        {
            "question": "What payment methods do you accept?",
            "answer": "We accept all major credit cards, PayPal, and Apple Pay for a secure checkout experience.",
            "category": "Payments"
        },
        {
            "question": "How do I choose the right size?",
            "answer": "We have a detailed size guide on every product page. You can also use our **✨ AI Stylist** to get a personalized size recommendation based on your height and weight!",
            "category": "Sizing"
        },
        {
            "question": "Do you have a loyalty program?",
            "answer": "Yes! Our **Elegance Club** lets you earn points on every purchase. Points can be redeemed for exclusive discounts and early access to new collections.",
            "category": "Loyalty"
        },
        {
            "question": "How do I apply a coupon code?",
            "answer": "You can enter your coupon code at the **Checkout** page under the 'Order Summary' section. The discount will be applied instantly to your total.",
            "category": "Discounts"
        },
        {
            "question": "Can I cancel my order?",
            "answer": "Orders can be cancelled within **1 hour** of placement. After that, they enter the processing stage, but you can still return the item once it arrives.",
            "category": "Orders"
        },
        {
            "question": "Where are your clothes made?",
            "answer": "Our clothes are ethically designed in **Kochi** and manufactured with premium fabrics sourced from sustainable partners across India.",
            "category": "About Us"
        },
        {
            "question": "Do you offer custom tailoring?",
            "answer": "Yes! As our name suggests, we specialize in **Tailored Elegance**. You can book a measurement session at our Kochi studio or provide custom measurements in your profile.",
            "category": "Services"
        },
        {
            "question": "How should I wash my premium shirts?",
            "answer": "We recommend a cold machine wash with similar colors. For our premium silk and linen blends, **Dry Cleaning** is highly recommended to preserve the fabric quality.",
            "category": "Care Guide"
        },
        {
            "question": "Can I change my shipping address?",
            "answer": "If your order hasn't been shipped yet, we can update your address! Please contact support at **+91 987 654 3210** immediately with your order ID.",
            "category": "Shipping"
        },
        {
            "question": "Are there any physical stores?",
            "answer": "Our flagship 'Tailored Elegance' studio is located in **Kochi, Kerala**. We are primarily an online-first brand but we do offer in-person styling by appointment.",
            "category": "About Us"
        },
        {
            "question": "Do you provide gift wrapping?",
            "answer": "Absolutely! You can select the **'Gift Wrap'** option during checkout for a premium packaging experience and a personalized note.",
            "category": "Services"
        }
    ]

    for faq in sample_faqs:
        obj, created = FAQ.objects.update_or_create(
            question=faq['question'],
            defaults={'answer': faq['answer'], 'category': faq['category']}
        )
        if created:
            print(f"Created FAQ: {faq['question']}")
        else:
            print(f"Updated FAQ: {faq['question']}")

if __name__ == "__main__":
    seed_faqs()
