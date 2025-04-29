// Dữ liệu mẫu cho các sản phẩm
const products = [
    { id: 1, name: "Điện thoại iPhone", category: "Điện thoại", price: 10000000 },
    { id: 2, name: "Laptop Dell", category: "Laptop", price: 20000000 },
    { id: 3, name: "Tai nghe Sony", category: "Phụ kiện", price: 1500000 },
    { id: 4, name: "Máy tính bảng Samsung", category: "Điện tử", price: 7000000 },
    { id: 5, name: "Điện thoại Samsung", category: "Điện thoại", price: 8000000 },
    { id: 6, name: "Máy tính xách tay HP", category: "Laptop", price: 18000000 },
];

// Hàm để hiển thị sản phẩm tìm kiếm được
function displayResults(results) {
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = ''; // Xóa kết quả cũ trước khi hiển thị kết quả mới

    if (results.length === 0) {
        resultsDiv.innerHTML = "<p>Không có sản phẩm nào phù hợp với từ khóa tìm kiếm.</p>";
        return;
    }

    results.forEach(product => {
        const productDiv = document.createElement("div");
        productDiv.classList.add("product");

        productDiv.innerHTML = `
            <div class="product-info">
                <div class="info-line"><strong>Tên sản phẩm:</strong> ${product.name}</div>
                <div class="info-line"><strong>Danh mục:</strong> ${product.category}</div>
                <div class="info-line"><strong>Giá:</strong> ${product.price.toLocaleString()} VND</div>
            </div>
        `;
        resultsDiv.appendChild(productDiv);
    });
}

// Hàm xử lý tìm kiếm trực tiếp khi nhập từ khóa
document.getElementById("keyword").addEventListener("input", function() {
    const keyword = this.value.toLowerCase(); // Lấy từ khóa tìm kiếm
    const filteredProducts = products.filter(product => product.name.toLowerCase().includes(keyword));

    displayResults(filteredProducts); // Hiển thị kết quả tìm kiếm
});
