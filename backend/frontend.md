# LifeTech4Code Frontend Design 

## API Documentation

### Authentication Endpoints

#### Discord OAuth Login
- **GET** `/auth/discord/login`
  - Initiates Discord OAuth2 login flow
  - Redirects to Discord authorization page
  - No request body needed

#### Discord OAuth Callback
- **GET** `/auth/discord/callback`
  - Handles Discord OAuth2 callback
  - Query parameters:
    - `code`: OAuth authorization code
    - `state`: State parameter for security

#### Get Current User Profile
- **GET** `/me`
  - Returns current user profile
  - Response:
    ```typescript
    {
      id: UUID
      email: string | null
      username: string
      display_name: string | null
      avatar_url: string | null
      phone_number: string | null
    }
    ```

#### Logout
- **POST** `/logout`
  - Logs out current user
  - No request/response body

### System Administration

#### Worker Management

##### Register Worker
- **POST** `/workers/register`
  - Register a new worker node
  - Request:
    ```typescript
    {
      token_id: UUID
      admin_token: string
      base_url: string
      name?: string
    }
    ```
  - Response:
    ```typescript
    {
      worker_id: UUID
    }
    ```

##### Worker Status Update
- **POST** `/workers/callback/status`
  - Update worker status and metrics
  - Headers required:
    - `X-Worker-Id`: UUID
    - `X-Timestamp`: number
    - `X-Signature`: string
  - Request:
    ```typescript
    {
      current_jobs: number
      net_mbps?: number
      req_rate?: number
    }
    ```

##### Worker Checklist Update
- **POST** `/workers/callback/checklist`
  - Update session checklist items
  - Headers required:
    - `X-Worker-Id`: UUID
    - `X-Timestamp`: number
    - `X-Signature`: string
  - Request:
    ```typescript
    {
      session_id: UUID
      items: Array<{
        key: string
        label: string
        done: boolean
        ts: string
        meta?: any
      }>
    }
    ```

##### Worker Result Update
- **POST** `/workers/callback/result`
  - Update session final result
  - Headers required:
    - `X-Worker-Id`: UUID
    - `X-Timestamp`: number
    - `X-Signature`: string
  - Request:
    ```typescript
    {
      session_id: UUID
      status: "ready" | "failed"
      rdp_host?: string
      rdp_port?: number
      rdp_user?: string
      rdp_password?: string
      log_url?: string
    }
    ```

#### Settings Management

##### Get Setting
- **GET** `/admin/settings/{key}`
  - Get system setting by key
  - Permission required: `settings:read`
  - Response: Setting value object

##### Update Setting
- **PUT** `/admin/settings/{key}`
  - Update system setting
  - Permission required: `settings:update`
  - Request: Setting value object
  - Response: Updated setting value

#### Audit Logging

##### List Audit Logs
- **GET** `/admin/audit`
  - List audit log entries
  - Permission required: `audit:read`
  - Query parameters:
    - `page`: Page number
    - `page_size`: Items per page
    - `action`: Filter by action type
    - `target_type`: Filter by target type
    - `actor`: Filter by actor user ID
    - `from`: Start date
    - `to`: End date
  - Response:
    ```typescript
    {
      items: Array<{
        id: UUID
        actor_user_id: UUID | null
        action: string
        target_type: string
        target_id: string | null
        diff_json: object | null
        ip: string | null
        ua: string | null
        created_at: string
      }>
      total: number
      page: number
      page_size: number
    }
    ```

### User Management

##### Create User
- **POST** `/admin/users`
  - Creates a new user
  - Permission required: `user:create`
  - Request:
    ```typescript
    {
      discord_id: string
      username: string
      email?: string
      display_name?: string
      avatar_url?: string
      phone_number?: string
    }
    ```
  - Response: AdminUser object

##### List Users
- **GET** `/admin/users`
  - Lists users with pagination
  - Permission required: `user:read`
  - Query parameters:
    - `q`: Search query
    - `page`: Page number (min: 1)
    - `page_size`: Items per page (1-100)
    - `role`: Filter by role UUID
  - Response:
    ```typescript
    {
      items: Array<AdminUser>
      total: number
      page: number
      page_size: number
    }
    ```

##### Get User Details
- **GET** `/admin/users/{user_id}`
  - Get specific user details
  - Permission required: `user:read`
  - Response: AdminUser object

##### Update User
- **PATCH** `/admin/users/{user_id}`
  - Update user details
  - Permission required: `user:update`
  - Request:
    ```typescript
    {
      username?: string
      email?: string
      display_name?: string
      avatar_url?: string
      phone_number?: string
    }
    ```
  - Response: AdminUser object

##### Delete User
- **DELETE** `/admin/users/{user_id}`
  - Delete a user
  - Permission required: `user:delete`
  - No response body

##### Manage User Roles
- **POST/DELETE** `/admin/users/{user_id}/roles`
  - Assign/remove roles from user
  - Permission required: `user:assign-role`
  - Request:
    ```typescript
    {
      role_ids: Array<UUID>
    }
    ```
  - Response: AdminUser object

##### Update User Coins
- **PATCH** `/admin/users/{user_id}/coins`
  - Update user's coin balance
  - Permission required: `user:coins:update`
  - Request:
    ```typescript
    {
      op: "add" | "subtract"
      amount: number
      reason?: string
    }
    ```
  - Response: AdminUser object

#### Role Management

##### Create Role
- **POST** `/admin/roles`
  - Create new role
  - Permission required: `role:create`
  - Request:
    ```typescript
    {
      name: string
      description?: string
    }
    ```
  - Response: RoleDTO object

##### List Roles
- **GET** `/admin/roles`
  - List all roles
  - Permission required: `role:read`
  - Response: Array<RoleDTO>

##### Get Role Details
- **GET** `/admin/roles/{role_id}`
  - Get specific role details
  - Permission required: `role:read`
  - Response: RoleDTO object

##### Update Role
- **PATCH** `/admin/roles/{role_id}`
  - Update role details
  - Permission required: `role:update`
  - Request:
    ```typescript
    {
      name?: string
      description?: string
    }
    ```
  - Response: RoleDTO object

##### Delete Role
- **DELETE** `/admin/roles/{role_id}`
  - Delete a role
  - Permission required: `role:delete`
  - No response body

##### Set Role Permissions
- **PUT** `/admin/roles/{role_id}/perms`
  - Set permissions for a role
  - Permission required: `role:set-perms`
  - Request:
    ```typescript
    {
      permission_codes: Array<string>
    }
    ```
  - Response: RoleDTO object

### VPS Management

#### List VPS Products
- **GET** `/vps/products`
  - Returns available VPS products
  - Query parameters:
    - `active`: boolean (filter active products only)
  - Response:
    ```typescript
    [
      {
        id: UUID
        name: string
        description: string | null
        price_coins: number
        is_active: boolean
      }
    ]
    ```

#### Purchase and Create VPS
- **POST** `/vps/purchase-and-create`
  - Creates new VPS session
  - Headers required:
    - `Idempotency-Key`: string
  - Request:
    ```typescript
    {
      product_id: UUID
    }
    ```
  - Response:
    ```typescript
    {
      session: {
        id: UUID
        status: "pending" | "provisioning" | "ready" | "failed" | "expired" | "deleted"
        checklist: Array<{
          key: string
          label: string
          done: boolean
          ts: string
          meta?: any
        }>
        created_at: string
        updated_at: string
        expires_at: string | null
        stream?: string // SSE endpoint URL
        rdp?: {
          host: string
          port: number
          user: string
          password: string
        }
        log_url?: string
      }
    }
    ```

#### Get VPS Session
- **GET** `/vps/sessions/{session_id}`
  - Get details of specific VPS session
  - Response: Same as session object above

#### Delete VPS Session
- **DELETE** `/vps/sessions/{session_id}`
  - Deletes/terminates VPS session
  - No response body

#### Stream Session Events
- **GET** `/vps/sessions/{session_id}/events`
  - SSE endpoint for real-time session updates
  - Event types:
    - `status.update`: Status changes
    - `checklist.update`: Checklist item updates

### Support System

#### List Support Threads
- **GET** `/support/threads`
  - Lists all support threads for user
  - Response:
    ```typescript
    {
      threads: Array<{
        id: UUID
        source: "ai" | "human"
        status: "open" | "pending" | "resolved" | "closed"
        created_at: string
        updated_at: string
        messages: Array<{
          id: UUID
          sender: string
          role: "user" | "assistant"
          content: string
          meta: any
          created_at: string
        }>
      }>
    }
    ```

#### Get Support Thread
- **GET** `/support/threads/{thread_id}`
  - Get specific support thread
  - Response: Same as thread object above

#### Ask AI Assistant
- **POST** `/support/ask`
  - Start AI conversation/get AI help
  - Request:
    ```typescript
    {
      message: string
    }
    ```
  - Response: Thread object

#### Create Human Support Thread
- **POST** `/support/threads`
  - Create new human support thread
  - Request:
    ```typescript
    {
      message: string
    }
    ```
  - Response: Thread object

#### Post Message to Thread
- **POST** `/support/threads/{thread_id}/message`
  - Add message to existing thread
  - Request:
    ```typescript
    {
      message: string
    }
    ```
  - Response: Updated thread object

### Ads System

#### Start Ad Session
- **POST** `/ads/start`
  - Initiates new ad viewing session
  - Response:
    ```typescript
    {
      nonce: string
    }
    ```

#### Claim Ad Reward
- **POST** `/ads/claim`
  - Claims reward for viewed ad
  - Request:
    ```typescript
    {
      nonce: string
      provider: "adsense" | "monetag"
      proof: Record<string, any>
    }
    ```
  - Response:
    ```typescript
    {
      claim: {
        id: UUID
        provider: string
        value_coins: number
        claimed_at: string
      }
      balance: number
    }
    ```

## Frontend Design Prompt

### Design Philosophy
Create a minimalist yet futuristic interface that emphasizes ease of use while maintaining a professional and tech-focused aesthetic. The design should follow these key principles:

1. **Clean & Modern**
   - Use a dark theme with accent colors
   - Implement smooth transitions and animations
   - Utilize ample white space
   - Apply glassmorphism effects for cards and containers

2. **Responsive & Intuitive**
   - Mobile-first approach
   - Smooth responsive breakpoints
   - Clear visual hierarchy
   - Intuitive navigation

3. **Visual Feedback**
   - Subtle hover effects
   - Loading states with skeleton screens
   - Success/error notifications
   - Progress indicators for long operations

### System Monitoring Interface

#### Worker Dashboard
- Worker status grid with:
  - Health indicators
  - Current load
  - Network metrics
  - Request rates
  - Active sessions
- Real-time metrics:
  - CPU/Memory usage
  - Network bandwidth
  - Request latency
  - Error rates
- Worker management:
  - Registration
  - Configuration
  - Load balancing settings

#### System Metrics Dashboard
- Resource utilization:
  - Database connections
  - Cache hit rates
  - Queue lengths
  - API latencies
- Error monitoring:
  - Error rates by endpoint
  - Failed sessions
  - Authentication failures
  - Rate limit hits
- Audit log viewer:
  - Advanced filtering
  - Timeline view
  - Action correlations
  - User activity trails

#### Settings Management
- Configuration categories:
  - System settings
  - Security policies
  - Rate limits
  - Feature flags
- Setting editors:
  - JSON schema validation
  - History tracking
  - Validation rules
  - Effect preview
- Deployment configs:
  - Environment variables
  - Service URLs
  - API keys
  - Integration settings

### Admin Interface Design

#### Dashboard Layout
- Top navigation bar with:
  - Logo/Brand
  - Quick search
  - User profile
  - Notifications
- Sidebar with:
  - User management
  - Role management
  - VPS management
  - Worker management
  - Support system
  - Analytics
  - Settings

#### Worker Management Interface
- Worker list view with:
  - Status indicators
  - Session counters
  - Product assignments
  - Quick actions
- Worker detail view:
  - Configuration
  - Active sessions
  - Performance metrics
  - Product mappings
  - Authentication status

#### VPS Product Management
- Product configuration with:
  - Worker assignments
  - Priority settings
  - Resource limits
  - Pricing tiers
- Worker mapping matrix:
  - Product-to-worker relationships
  - Load balancing rules
  - Failover settings

#### User Management Interface
- List view with:
  - Filterable table
  - Bulk actions
  - Quick edit
  - Role assignment
  - Coin balance management
    - Add/subtract coins
    - Transaction history
    - Balance adjustments
    - Audit logging
- VPS session management:
  - Active sessions
  - Session logs
  - RDP credentials
  - Resource usage
- User detail view with:
  - Profile information
  - Role assignments
  - Activity history
  - Support threads
  - VPS sessions

#### Role Management Interface
- Role list with:
  - Permissions matrix
  - User assignments
  - Drag-drop permission management
- Role detail with:
  - Permission assignments
  - User list
  - Audit log

### Color Scheme
```css
:root {
  --primary: #6C63FF;      /* Main brand color */
  --secondary: #FF6584;    /* Accent color */
  --success: #00C896;      /* Success states */
  --warning: #FFB74D;      /* Warning states */
  --error: #FF5252;        /* Error states */
  --background: #1A1B1E;   /* Main background */
  --surface: #2A2B2E;      /* Card background */
  --admin: #9C27B0;        /* Admin interface */
  --text-primary: #FFFFFF; /* Primary text */
  --text-secondary: #B0B0B0; /* Secondary text */
}
```

### Component Library

#### Navigation
- Sleek sidebar with icon+text navigation
- Collapsible on mobile
- Active state indicators
- Quick access toolbar for common actions
- Permission-based menu items

#### Admin-specific Components
- Permission Matrix
  - Grid layout
  - Checkbox interfaces
  - Bulk selection
  - Search/filter

- Role Manager
  - Drag-drop interface
  - Permission grouping
  - User assignment
  - Quick actions

- User Table
  - Sortable columns
  - Bulk actions
  - Inline editing
  - Status indicators

#### Cards
- Glassmorphism effect
- Subtle hover elevation
- Rounded corners
- Status indicators
- Action buttons in consistent locations

#### Forms
- Floating labels
- Inline validation
- Clear error messages
- Progress steps for multi-step forms
- Permission checks

### Key Screens

#### Admin Dashboard
- Key metrics overview
  - Active users
  - VPS usage
  - Support queue
  - Revenue stats
- Quick actions panel
- Recent activity feed
- System health status

#### User Management
- User list with filters
- Role assignment interface
- Coin management
- Activity monitoring
- Support case overview

#### Role Management
- Permission matrix
- User assignment
- Audit logging
- Bulk operations interface

#### System Monitoring
- VPS resource usage
- User activity
- Error logs
- Performance metrics

### Animations & Transitions

1. **Page Transitions**
   ```css
   .page-transition {
     transition: opacity 0.3s ease-in-out;
     animation: slideIn 0.4s ease-out;
   }
   ```

2. **Card Hover**
   ```css
   .card {
     transition: transform 0.2s ease, box-shadow 0.2s ease;
   }
   .card:hover {
     transform: translateY(-2px);
     box-shadow: 0 8px 16px rgba(0,0,0,0.2);
   }
   ```

3. **Status Updates**
   ```css
   .status-change {
     animation: pulse 0.5s ease-in-out;
   }
   ```

### Responsive Breakpoints
```css
/* Mobile first approach */
/* Base styles for mobile */

/* Tablet (768px and up) */
@media (min-width: 768px) {
  /* Tablet specific styles */
}

/* Desktop (1024px and up) */
@media (min-width: 1024px) {
  /* Desktop specific styles */
}

/* Large Desktop (1440px and up) */
@media (min-width: 1440px) {
  /* Large desktop specific styles */
}
```

### Loading States
1. **Skeleton Screens**
   - Use pulse animation
   - Match content layout
   - Subtle gradient effect

2. **Progress Indicators**
   - Circular for small actions
   - Linear for page-level operations
   - Percentage indicators for long processes

### Error Handling
1. **Toast Notifications**
   - Brief, informative messages
   - Color-coded by type
   - Auto-dismiss with manual option
   - Position consistent (top-right)

2. **Form Validation**
   - Real-time validation
   - Clear error messages
   - Visual indicators
   - Recovery suggestions

### Accessibility
- High contrast ratios
- Keyboard navigation
- ARIA labels
- Screen reader support
- Focus indicators

### Data Models & Validation

#### User Model
```typescript
interface User {
  id: UUID
  discord_id: string
  email?: string
  username: string
  display_name?: string
  avatar_url?: string
  phone_number?: string
  coins: number
  created_at: string
  updated_at: string
}
```

#### Worker Model
```typescript
interface Worker {
  id: UUID
  name?: string
  base_url: string
  token_id?: UUID
  status: "idle" | "busy" | "offline"
  current_jobs: number
  last_net_mbps?: number
  last_req_rate?: number
  last_heartbeat?: string
  created_at: string
}
```

#### VPS Product Model
```typescript
interface VpsProduct {
  id: UUID
  name: string
  description?: string
  price_coins: number
  is_active: boolean
  created_at: string
  updated_at: string
}
```

#### VPS Session Model
```typescript
interface VpsSession {
  id: UUID
  user_id?: UUID
  product_id?: UUID
  worker_id?: UUID
  session_token: string
  status: "pending" | "provisioning" | "ready" | "failed" | "expired" | "deleted"
  checklist: Array<{
    key: string
    label: string
    done: boolean
    ts: string
    meta?: any
  }>
  rdp_host?: string
  rdp_port?: number
  rdp_user?: string
  rdp_password?: string
  log_url?: string
  created_at: string
  updated_at: string
  expires_at?: string
  idempotency_key?: string
}
```

#### Ads Claim Model
```typescript
interface AdsClaim {
  id: UUID
  user_id?: UUID
  provider: "adsense" | "monetag"
  nonce: string
  value_coins: number
  claimed_at: string
  meta?: Record<string, any>
  created_at: string
}
```

#### Support Thread Model
```typescript
interface SupportThread {
  id: UUID
  user_id?: UUID
  source: "ai" | "human"
  status: "open" | "pending" | "resolved" | "closed"
  messages: Array<{
    id: UUID
    sender: string
    role: "user" | "assistant"
    content: string
    meta?: any
    created_at: string
  }>
  created_at: string
  updated_at: string
}
```

#### Role & Permission Models
```typescript
interface Role {
  id: UUID
  name: string
  description?: string
  permissions: Array<{
    id: UUID
    code: string
    description?: string
  }>
  created_at: string
  updated_at: string
}

interface Permission {
  id: UUID
  code: string
  description?: string
}
```

#### Audit Log Model
```typescript
interface AuditLog {
  id: UUID
  actor_user_id?: UUID
  action: string
  target_type: string
  target_id?: string
  diff_json?: Record<string, any>
  ip?: string
  ua?: string
  created_at: string
}
```

### Validation Rules

#### User Validation
- Username: 3-100 characters
- Email: Valid email format
- Phone: Optional, E.164 format
- Discord ID: Required, string format
- Coins: Non-negative integer

#### VPS Session Validation
- Valid product selection
- Active worker assignment
- Valid idempotency key
- Status transitions:
  - pending → provisioning
  - provisioning → ready/failed
  - ready → expired/deleted
  - failed → deleted

#### Support Thread Validation
- Valid source type
- Valid status transitions
- Message content required
- Valid role assignments

#### Worker Validation
- Valid base URL
- Valid token association
- Status consistency
- Metrics range validation

#### Role & Permission Validation
- Unique role names
- Valid permission codes
- Permission hierarchy
- Circular dependency check

### Performance Optimizations
1. **Code Splitting**
   - Route-based splitting
   - Component lazy loading
   - Dynamic imports

2. **Asset Optimization**
   - Image compression
   - SVG for icons
   - Font subsetting
   - Critical CSS

3. **Data Management**
   - Optimistic updates
   - Connection pooling
   - Query optimization
   - Cache strategies

4. **API Optimization**
   - Response compression
   - Batch requests
   - Rate limiting
   - Request coalescing

### Security Features
1. **Permission-based UI**
   - Dynamic menu items
   - Conditional rendering
   - Role-based access
   - Audit logging

2. **Data Protection**
   - Sensitive data masking
   - Session management
   - Activity monitoring
   - Secure forms

This design approach creates a modern, user-friendly interface that balances aesthetics with functionality, perfect for a technical platform while maintaining high usability standards. The admin interface is designed to be powerful yet intuitive, with a focus on efficient management of users, roles, and system resources.

USE Next.js