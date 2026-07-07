document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================================================
    // ACCOUNT DROPDOWN TOGGLE
    // ==========================================================================
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdownContent = document.getElementById('userDropdownContent');

    if (userMenuBtn && userDropdownContent) {
        userMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = userDropdownContent.style.display === 'block';
            userDropdownContent.style.display = isOpen ? 'none' : 'block';
        });

        document.addEventListener('click', function() {
            userDropdownContent.style.display = 'none';
        });
    }

    // ==========================================================================
    // LIVE AUTOCOMPLETE SEARCH SUGGESTIONS
    // ==========================================================================
    const searchInput = document.getElementById('searchInput');
    const searchSuggestions = document.getElementById('searchSuggestions');

    if (searchInput && searchSuggestions) {
        searchInput.addEventListener('input', debounce(function() {
            const query = searchInput.value.trim();
            if (query.length < 2) {
                searchSuggestions.style.display = 'none';
                searchSuggestions.innerHTML = '';
                return;
            }

            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        searchSuggestions.style.display = 'none';
                        searchSuggestions.innerHTML = '';
                        return;
                    }

                    searchSuggestions.innerHTML = '';
                    data.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'suggestion-item';
                        div.innerHTML = `
                            <img src="${item.image_url}" alt="${item.name}">
                            <div class="suggestion-details">
                                <span class="suggestion-name">${item.name}</span>
                                <span class="suggestion-price">₹${item.price.toLocaleString()}</span>
                            </div>
                        `;
                        div.addEventListener('click', function() {
                            window.location.href = `/product/${item.id}`;
                        });
                        searchSuggestions.appendChild(div);
                    });
                    searchSuggestions.style.display = 'block';
                })
                .catch(err => console.error('Error fetching suggestions:', err));
        }, 200));

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
                searchSuggestions.style.display = 'none';
            }
        });
    }

    // ==========================================================================
    // TOAST NOTIFICATIONS HELPER
    // ==========================================================================
    function showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast-msg';
        if (type === 'danger') {
            toast.style.borderLeftColor = 'var(--danger)';
        }
        
        toast.innerHTML = `
            <span>${message}</span>
        `;
        container.appendChild(toast);

        // Remove from DOM after animation completes (3 seconds total)
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // ==========================================================================
    // AJAX CART OPERATIONS
    // ==========================================================================
    
    // Add-to-cart triggers
    const addToCartBtns = document.querySelectorAll('.add-to-cart-btn');
    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const productId = btn.getAttribute('data-product-id');
            
            fetch('/api/cart/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ product_id: productId, quantity: 1 })
            })
            .then(res => {
                if (res.status === 401) {
                    // Redirect to login if unauthorized
                    showToast('Please log in to add items to your cart.', 'danger');
                    setTimeout(() => {
                        window.location.href = `/login?next=${encodeURIComponent(window.location.href)}`;
                    }, 1000);
                    throw new Error('Unauthorized');
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    showToast(data.message);
                    // Update header badge
                    const badge = document.getElementById('cartBadge');
                    if (badge) {
                        badge.textContent = data.cart_count;
                    }
                } else {
                    showToast(data.message || 'Failed to add item.', 'danger');
                }
            })
            .catch(err => {
                if (err.message !== 'Unauthorized') {
                    console.error('Error adding to cart:', err);
                }
            });
        });
    });

    // Buy-Now triggers
    const buyNowBtns = document.querySelectorAll('.buy-now-btn');
    buyNowBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const productId = btn.getAttribute('data-product-id');
            
            fetch('/api/cart/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ product_id: productId, quantity: 1 })
            })
            .then(res => {
                if (res.status === 401) {
                    showToast('Please log in to make a purchase.', 'danger');
                    setTimeout(() => {
                        window.location.href = `/login?next=${encodeURIComponent(window.location.href)}`;
                    }, 1000);
                    throw new Error('Unauthorized');
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    window.location.href = '/checkout';
                } else {
                    showToast(data.message || 'Failed to initialize purchase.', 'danger');
                }
            })
            .catch(err => {
                if (err.message !== 'Unauthorized') {
                    console.error('Error during Buy Now:', err);
                }
            });
        });
    });

    // ==========================================================================
    // DYNAMIC QUANTITY CONTROLS (CART PAGE)
    // ==========================================================================
    const cartLayout = document.getElementById('cartLayout');
    const emptyCartCard = document.getElementById('emptyCartCard');

    if (cartLayout) {
        // Minus Button
        cartLayout.addEventListener('click', function(e) {
            if (e.target.classList.contains('qty-minus')) {
                const productId = e.target.getAttribute('data-product-id');
                const qtyDisplay = document.getElementById(`qty-val-${productId}`);
                let currentQty = parseInt(qtyDisplay.textContent);
                
                if (currentQty <= 1) return; // cannot go below 1
                
                updateCartQuantity(productId, currentQty - 1);
            }
            
            // Plus Button
            if (e.target.classList.contains('qty-plus')) {
                const productId = e.target.getAttribute('data-product-id');
                const qtyDisplay = document.getElementById(`qty-val-${productId}`);
                let currentQty = parseInt(qtyDisplay.textContent);
                
                updateCartQuantity(productId, currentQty + 1);
            }

            // Remove Button
            if (e.target.classList.contains('remove-item-btn')) {
                const productId = e.target.getAttribute('data-product-id');
                removeCartItem(productId);
            }
        });
    }

    function updateCartQuantity(productId, newQty) {
        const warning = document.getElementById(`qty-warning-${productId}`);
        if (warning) warning.classList.add('hidden');

        fetch('/api/cart/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ product_id: productId, quantity: newQty })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Update elements
                document.getElementById(`qty-val-${productId}`).textContent = data.quantity;
                document.getElementById(`item-subtotal-${productId}`).textContent = '₹' + data.item_total.toLocaleString();
                
                updatePriceSummary(data);

                if (data.capped && warning) {
                    warning.classList.remove('hidden');
                    showToast('Capped at maximum stock limit.', 'danger');
                }
            }
        })
        .catch(err => console.error('Error updating quantity:', err));
    }

    function removeCartItem(productId) {
        fetch('/api/cart/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ product_id: productId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Remove row
                const row = document.getElementById(`cartItemRow-${productId}`);
                if (row) row.remove();

                // Check empty state
                if (data.is_empty) {
                    cartLayout.classList.add('hidden');
                    emptyCartCard.classList.remove('hidden');
                } else {
                    updatePriceSummary(data);
                }
                
                // Update header badge
                const badge = document.getElementById('cartBadge');
                if (badge) badge.textContent = data.cart_count;

                showToast('Product removed from cart.');
            }
        })
        .catch(err => console.error('Error removing item:', err));
    }

    function updatePriceSummary(data) {
        const subtotalEl = document.getElementById('summary-subtotal');
        const discountEl = document.getElementById('summary-discount');
        const shippingEl = document.getElementById('summary-shipping');
        const totalEl = document.getElementById('summary-total');
        const countEl = document.getElementById('summary-count');
        const savingsEl = document.getElementById('summary-savings');

        if (subtotalEl) subtotalEl.textContent = '₹' + data.subtotal.toLocaleString();
        if (discountEl) discountEl.textContent = '-₹' + data.discount.toLocaleString();
        if (savingsEl) savingsEl.textContent = '₹' + data.discount.toLocaleString();
        if (countEl) countEl.textContent = data.cart_count;
        
        if (shippingEl) {
            if (data.shipping === 0) {
                shippingEl.innerHTML = '<strong class="text-success">FREE</strong>';
            } else {
                shippingEl.textContent = '₹' + data.shipping.toLocaleString();
            }
        }
        if (totalEl) totalEl.textContent = '₹' + data.total.toLocaleString();
    }

    // ==========================================================================
    // PAYMENT METHOD CONDITIONAL FIELDS (CHECKOUT PAGE)
    // ==========================================================================
    const payCOD = document.getElementById('payCOD');
    const payUPI = document.getElementById('payUPI');
    const payCard = document.getElementById('payCard');
    
    const upiFields = document.getElementById('upiFields');
    const cardFields = document.getElementById('cardFields');

    if (payCOD && payUPI && payCard) {
        const radios = [payCOD, payUPI, payCard];
        
        radios.forEach(radio => {
            radio.addEventListener('change', function() {
                // Clear active classes on labels
                document.querySelectorAll('.payment-option-card').forEach(card => {
                    card.classList.remove('active');
                });
                
                // Add active to parent label
                radio.closest('.payment-option-card').classList.add('active');

                // Toggle conditional sections
                if (payUPI.checked) {
                    upiFields.classList.remove('hidden');
                    cardFields.classList.add('hidden');
                    document.getElementById('upiIdInput').setAttribute('required', 'required');
                    clearCardValidation();
                } else if (payCard.checked) {
                    cardFields.classList.remove('hidden');
                    upiFields.classList.add('hidden');
                    document.getElementById('cardNumberInput').setAttribute('required', 'required');
                    document.getElementById('cardExpiryInput').setAttribute('required', 'required');
                    document.getElementById('cardCvvInput').setAttribute('required', 'required');
                    document.getElementById('upiIdInput').removeAttribute('required');
                } else {
                    upiFields.classList.add('hidden');
                    cardFields.classList.add('hidden');
                    document.getElementById('upiIdInput').removeAttribute('required');
                    clearCardValidation();
                }
            });
        });
    }

    function clearCardValidation() {
        document.getElementById('cardNumberInput')?.removeAttribute('required');
        document.getElementById('cardExpiryInput')?.removeAttribute('required');
        document.getElementById('cardCvvInput')?.removeAttribute('required');
    }

    // ==========================================================================
    // HERO BANNER CAROUSEL SLIDER LOGIC
    // ==========================================================================
    const slides = document.querySelectorAll('.hero-slide');
    const dots = document.querySelectorAll('.slider-dots .dot');
    const prevBtn = document.getElementById('prevSlideBtn');
    const nextBtn = document.getElementById('nextSlideBtn');
    
    if (slides.length > 0) {
        let currentSlideIndex = 0;
        let slideInterval = setInterval(nextSlide, 4500);

        function showSlide(index) {
            // Cap indexes
            if (index >= slides.length) currentSlideIndex = 0;
            else if (index < 0) currentSlideIndex = slides.length - 1;
            else currentSlideIndex = index;

            // Update DOM classes
            slides.forEach(slide => slide.classList.remove('active'));
            dots.forEach(dot => dot.classList.remove('active'));

            slides[currentSlideIndex].classList.add('active');
            dots[currentSlideIndex].classList.add('active');
        }

        function nextSlide() {
            showSlide(currentSlideIndex + 1);
        }

        function prevSlide() {
            showSlide(currentSlideIndex - 1);
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                nextSlide();
                resetInterval();
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                prevSlide();
                resetInterval();
            });
        }

        dots.forEach(dot => {
            dot.addEventListener('click', () => {
                const idx = parseInt(dot.getAttribute('data-slide-index'));
                showSlide(idx);
                resetInterval();
            });
        });

        function resetInterval() {
            clearInterval(slideInterval);
            slideInterval = setInterval(nextSlide, 4500);
        }
    }

    // ==========================================================================
    // ADMIN DASHBOARD CONTROLS (ORDERS & STOCK INVENTORY)
    // ==========================================================================
    
    // 1. Update Order Status
    const statusSelects = document.querySelectorAll('.status-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const orderId = select.getAttribute('data-order-id');
            const newStatus = select.value;
            const badge = document.getElementById(`statusBadge-${orderId}`);

            fetch('/api/admin/order/status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ order_id: orderId, status: newStatus })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message);
                    
                    // Update badge text and classes
                    if (badge) {
                        badge.textContent = newStatus;
                        badge.className = `status-badge ${newStatus.toLowerCase()}`;
                    }
                } else {
                    showToast(data.message || 'Failed to update order status.', 'danger');
                }
            })
            .catch(err => console.error('Error updating order status:', err));
        });
    });

    // 2. Restock Inventory
    const saveStockBtns = document.querySelectorAll('.btn-save-stock');
    saveStockBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const productId = btn.getAttribute('data-product-id');
            const input = document.getElementById(`stockInput-${productId}`);
            const cell = document.getElementById(`stockCell-${productId}`);
            const newStockVal = input.value;

            if (newStockVal === '' || parseInt(newStockVal) < 0) {
                showToast('Please enter a valid stock value.', 'danger');
                return;
            }

            fetch('/api/admin/product/stock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ product_id: productId, stock: newStockVal })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message);
                    
                    // Update stock cell
                    if (cell) {
                        cell.textContent = `${newStockVal} units`;
                        if (parseInt(newStockVal) <= 5) {
                            cell.classList.add('low');
                        } else {
                            cell.classList.remove('low');
                        }
                    }
                } else {
                    showToast(data.message || 'Failed to update stock.', 'danger');
                }
            })
            .catch(err => console.error('Error updating product stock:', err));
        });
    });

    // ==========================================================================
    // WISHLIST TOGGLE OPERATIONS
    // ==========================================================================
    
    // Toggling from anywhere (homepage cards, details page, category pages)
    document.querySelectorAll('.wishlist-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const productId = btn.getAttribute('data-product-id');
            toggleWishlist(productId, btn);
        });
    });

    // Removals from wishlist page badge button
    document.querySelectorAll('.remove-wishlist-badge-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const productId = btn.getAttribute('data-product-id');
            toggleWishlist(productId, null, true);
        });
    });

    function toggleWishlist(productId, btnElement, isWishlistPageRemoval = false) {
        fetch('/api/wishlist/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ product_id: productId })
        })
        .then(res => {
            if (res.status === 401) {
                showToast('Please log in to save items to your wishlist.', 'danger');
                setTimeout(() => {
                    window.location.href = `/login?next=${encodeURIComponent(window.location.href)}`;
                }, 1000);
                throw new Error('Unauthorized');
            }
            return res.json();
        })
        .then(data => {
            if (data.success) {
                showToast(data.message);
                
                // Update badge in header
                const badge = document.getElementById('wishlistBadge');
                if (badge) badge.textContent = data.wishlist_count;

                // If removing from the wishlist page, hide the row/card immediately
                if (isWishlistPageRemoval || (window.location.pathname === '/wishlist' && data.state === 'removed')) {
                    const card = document.getElementById(`wishlistItem-${productId}`);
                    if (card) {
                        card.remove();
                        // If wishlist becomes empty, toggle view
                        const grid = document.getElementById('wishlistGrid');
                        const emptyCard = document.getElementById('emptyWishlistCard');
                        const remaining = grid ? grid.querySelectorAll('.product-card') : [];
                        if (remaining.length === 0 && emptyCard) {
                            if (grid) grid.classList.add('hidden');
                            emptyCard.classList.remove('hidden');
                        }
                    }
                } else if (btnElement) {
                    // Update visual state of clicked heart button
                    if (data.state === 'added') {
                        btnElement.classList.add('active');
                        btnElement.textContent = '❤️';
                    } else {
                        btnElement.classList.remove('active');
                        btnElement.textContent = '🤍';
                    }
                }
            } else {
                showToast(data.message || 'Failed to update wishlist.', 'danger');
            }
        })
        .catch(err => {
            if (err.message !== 'Unauthorized') {
                console.error('Error toggling wishlist:', err);
            }
        });
    }

    // ==========================================================================
    // CHECKOUT PROMO COUPON LOGIC
    // ==========================================================================
    const applyPromoBtn = document.getElementById('applyPromoBtn');
    const promoCodeInput = document.getElementById('promoCodeInput');
    const promoMessage = document.getElementById('promoMessage');
    const hiddenPromoInput = document.getElementById('hiddenPromoInput');
    const couponDiscountRow = document.getElementById('couponDiscountRow');
    const checkoutCouponDiscount = document.getElementById('checkoutCouponDiscount');
    const checkoutTotalVal = document.getElementById('checkoutTotalVal');

    if (applyPromoBtn && promoCodeInput) {
        applyPromoBtn.addEventListener('click', function() {
            validateAndApplyCoupon();
        });

        promoCodeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                validateAndApplyCoupon();
            }
        });
    }

    function validateAndApplyCoupon() {
        const code = promoCodeInput.value.trim();
        if (!code) {
            showToast('Please enter a coupon code.', 'danger');
            return;
        }

        fetch('/api/checkout/coupon', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ promo_code: code })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Update hidden input
                if (hiddenPromoInput) hiddenPromoInput.value = code;

                // Show success message
                if (promoMessage) {
                    promoMessage.textContent = data.message;
                    promoMessage.className = 'promo-message text-success';
                }

                // Show discount breakdown
                if (couponDiscountRow && checkoutCouponDiscount) {
                    checkoutCouponDiscount.textContent = `-₹${data.coupon_discount.toLocaleString()}`;
                    couponDiscountRow.classList.remove('hidden');
                }

                // Update grand total
                if (checkoutTotalVal) {
                    checkoutTotalVal.textContent = `₹${data.new_total.toLocaleString()}`;
                }

                showToast('Promo code applied successfully!');
            } else {
                // Reset states on failure
                if (hiddenPromoInput) hiddenPromoInput.value = '';
                if (couponDiscountRow) couponDiscountRow.classList.add('hidden');
                
                if (promoMessage) {
                    promoMessage.textContent = data.message || 'Invalid coupon code.';
                    promoMessage.className = 'promo-message text-danger';
                }
                
                showToast(data.message || 'Failed to apply coupon.', 'danger');
            }
        })
        .catch(err => console.error('Error applying coupon:', err));
    }

    // ==========================================================================
    // DEBOUNCE FUNCTION
    // ==========================================================================
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

});
